"""
fs_sse.py —— 稳健版 fs-server MCP SSE 客户端
修复原客户端 6 个抖动根因：
  1) SSE 流断开自动重连 + 重新 handshake（核心）
  2) 捕获 POST 200 body 中的内联 JSON-RPC 结果（Streamable HTTP）
  3) 用 threading.Event 替代忙轮询，响应到达即刻唤醒
  4) 指数退避 + 抖动，避免失败风暴
  5) 正确处理多行 data: 事件边界
  6) 请求串行 + 轻微限速，降低服务端丢包
"""
import urllib.request, urllib.error, json, threading, time, random

class FsMCP:
    def __init__(self, base, auth, host, connect_timeout=30, verbose=False):
        self.base = base
        self.auth = auth
        self.host = host
        self.connect_timeout = connect_timeout
        self.verbose = verbose
        self.lock = threading.Lock()
        self.responses = {}            # cid -> (obj_or_None, Event)
        self.endpoint = None
        self.msg_url = None
        self.ready = threading.Event()
        self.stop = False
        self._init_id = 0
        self.thread = threading.Thread(target=self._sse_loop, daemon=True)
        self.thread.start()
        # 等待首次握手就绪（最多 30s）
        self.ready.wait(timeout=30)

    # ---------------- SSE 读取 + 自动重连 ----------------
    def _sse_loop(self):
        while not self.stop:
            try:
                req = urllib.request.Request(self.base, headers={
                    "Accept": "text/event-stream",
                    "Authorization": self.auth,
                    "Cache-Control": "no-cache"})
                resp = urllib.request.urlopen(req, timeout=self.connect_timeout)
            except Exception as e:
                if self.verbose: print("[SSE] connect fail:", e)
                time.sleep(1.0 + random.random())
                continue
            # 新连接 -> 重置 session 状态
            with self.lock:
                self.endpoint = None
                self.msg_url = None
                self.ready.clear()
            ev = None
            buf = []
            try:
                for raw in resp:
                    line = raw.decode('utf-8', 'replace').rstrip('\n').rstrip('\r')
                    if line == '':                       # 事件边界
                        self._dispatch(ev, buf)
                        ev, buf = None, []
                    elif line.startswith('event:'):
                        ev = line[6:].strip()
                    elif line.startswith('data:'):
                        buf.append(line[5:].strip())
                    # ':' 开头为注释/心跳，忽略
            except Exception as e:
                if self.verbose: print("[SSE] stream break:", e)
            # 流结束/断开 -> 循环顶部自动重连
            if not self.stop:
                time.sleep(0.3)

    def _dispatch(self, ev, buf):
        text = '\n'.join(buf)
        if not text:
            return
        if ev == 'endpoint':
            with self.lock:
                self.endpoint = text
                self.msg_url = (self.host + text) if text.startswith('/') else text
            self._handshake()          # 拿到 endpoint 立刻握手
            return
        if ev == 'message':
            try:
                o = json.loads(text)
            except Exception:
                return
            self._store(o)

    def _store(self, o):
        cid = o.get('id')
        if cid is None:
            return
        with self.lock:
            if cid in self.responses:
                ev = self.responses[cid][1]
                self.responses[cid] = (o, ev)
            else:
                ev = threading.Event()
                self.responses[cid] = (o, ev)
            ev.set()

    def _handshake(self):
        with self.lock:
            if not self.msg_url:
                return
        # initialize
        self._raw_post({"jsonrpc": "2.0",
                        "id": "init_" + str(int(time.time() * 1000)),
                        "method": "initialize",
                        "params": {"protocolVersion": "2025-06-18",
                                   "capabilities": {},
                                   "clientInfo": {"name": "x", "version": "1"}}})
        time.sleep(0.8)
        self._raw_post({"jsonrpc": "2.0",
                        "method": "notifications/initialized", "params": {}})
        with self.lock:
            self.ready.set()

    # ---------------- POST（同时兜底内联结果） ----------------
    def _raw_post(self, payload):
        with self.lock:
            if not self.msg_url:
                return None
            url = self.msg_url
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={
            "Content-Type": "application/json",
            "Authorization": self.auth,
            "Accept": "application/json, text/event-stream"})
        try:
            body = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if self.verbose: print("[POST] HTTP", e.code)
            return "HTTP %s" % e.code
        except Exception as e:
            if self.verbose: print("[POST] fail:", e)
            return None
        # Streamable HTTP：结果可能直接回在 POST body
        if body:
            try:
                o = json.loads(body)
                if isinstance(o, dict) and 'id' in o and ('result' in o or 'error' in o):
                    self._store(o)
            except Exception:
                pass
        return body

    # ---------------- 对外调用 ----------------
    def call(self, method, params, cid=None, timeout=60):
        if cid is None:
            with self.lock:
                self._init_id += 1
                cid = "c%d_%d" % (self._init_id, int(time.time() * 1000))
        with self.lock:
            if cid not in self.responses:
                self.responses[cid] = (None, threading.Event())
            ev = self.responses[cid][1]
        # 未就绪则等握手（最多 10s），避免用过期 session POST
        if not self.ready.is_set():
            self.ready.wait(timeout=10)
        time.sleep(0.05)              # 轻微限速，抑制突发
        self._raw_post({"jsonrpc": "2.0", "id": cid, "method": method, "params": params})
        ev.wait(timeout=timeout)
        with self.lock:
            item = self.responses.pop(cid, None)
        return item[0] if item else None

    def query(self, sql, tries=6, timeout=60):
        for i in range(tries):
            cid = "q%d_%d_%d" % (i, int(time.time() * 1000), random.randint(0, 9999))
            res = self.call("tools/call",
                            {"apiName": "QueryRecordsBySQL", "sql": sql},
                            cid=cid, timeout=timeout)
            if res is None:
                if self.verbose:
                    print("  [query] 无响应, backoff %.1fs" % (0.5 * 2 ** i))
                time.sleep(0.5 * (2 ** i) + random.random())
                continue
            try:
                c = res.get('result', {}).get('content', [{}])[0].get('text', '')
                o = json.loads(c)
                if o.get('resultCode') != 'SUCCESS':
                    time.sleep(0.5 * (2 ** i) + random.random())
                    continue
                recs = o['data']['recordResult']['records']
                lr = o['data'].get('queryMeta', {}).get('limitReached')
                return recs, lr
            except Exception:
                time.sleep(0.5 * (2 ** i) + random.random())
                continue
        return None, None

    def close(self):
        self.stop = True


if __name__ == '__main__':
    # 自测：用你环境里的真实凭证跑一条查询
    import os
    BASE = "https://open.fxiaoke.com/mcp/hzxfdq/001-01"
    AUTH = "FSUTK_E9B10254A52BD6FB59E6218A0692E4FE6508F5AA337AB49137DCADDDB25099EB"
    HOST = "https://open.fxiaoke.com"
    m = FsMCP(BASE, AUTH, HOST, verbose=True)
    t0 = time.time()
    recs, lr = m.query("select _id,name from commission_base_table__c where owner='1748' limit 3", tries=4)
    dt = time.time() - t0
    print("cost=%.2fs recs=%s limitReached=%s" % (dt, len(recs) if recs else None, lr))
    if recs:
        for r in recs[:3]:
            print("  ", r.get('name'))
    m.close()
