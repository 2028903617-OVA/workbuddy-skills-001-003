# sharecrm程序安装步聚
## 检查本机是否已经安装了sharecrm程序
- 使用以下命令查看本机是否已经安装sharecrm程序
```shell
  sharecrm -V
```
- 如果已经安装sharecrm程序，则返回sharecrm版本信息
- 如果未安装sharecrm程序，则会返回如下信息
```text
  command not found: sharecrm
```

## 安装sharecrm程序
### 依赖项检查（node.js）
- 使用以下命令检查本机是否已经安装node.js
```shell
  node -v
```
- 如果已经安装node.js，则返回node.js版本信息
- 如果未安装node.js，则会返回如下信息
```text
  command not found: node
```
- Windows系统下安装node.js
- 访问[node.js官网](https://nodejs.org/en/)下载node.js安装包并安装
- linux系统直接执行以下命令安装node.js
```shell
  curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
  sudo apt install -y nodejs
```
- macos系统直接执行以下命令安装node.js
```shell
  brew install node
```
- 检查node.js安装成功
```shell
  node -v
```
### 安装sharecrm
```shell
  npm install sharecrm -g
```
- 安装成功后，使用以下命令查看sharecrm版本信息
```shell
  sharecrm -V
```