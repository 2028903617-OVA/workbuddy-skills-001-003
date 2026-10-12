### `sharecrm file`

文件相关本地命令,主要用与对象的文件类型字段值的生成，。

用法：

```shell
sharecrm file [command]
```

| 子命令 | 描述 |
|:---|:---|
| `upload` | Upload a file |
| `help [command]` | display help for command |

#### `sharecrm file upload`

上传本地文件，成功后输出生成下载链接接口返回的 `data` 对象 JSON，并附加 `size`、`filename`、`ext` 字段。

用法：

```shell
sharecrm file upload --file /path/to/demo.txt --resourceType N --fileName demo.txt --extension txt
```

参数：

| 参数 | 是否必填 | 说明 |
|:---|:---|:---|
| `--file` | 是 | 本地文件路径 |
| `--resourceType` | 否 | 上传文件类型，如 `N`、`TN`，默认 `TN` |
| `--fileName` | 否 | 文件名；未传时从 `--file` 路径推导 |
| `--extension` | 否 | 文件扩展名；未传时从文件名/路径推导，仍为空则 `bin` |

成功返回结果：

```json
{
    "path":"TN_425c1feaa36947eeadc6476426a84a49", // 文件ID，Path名称
    "url":"文件下载链接", // 文件下载地址
    "size":1760,   // 文件大小
    "filename":"ScreenShot_2026-05-28_163014_640.png", // 文件名称
    "ext":"png" // 文件扩展
}
```
