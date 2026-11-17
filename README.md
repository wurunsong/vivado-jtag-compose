# Vivado Lab JTAG 容器配置

在 x86-64 Ubuntu 上运行 Vivado Lab 2018.3。默认配置启动一个容器，也可以选择两路或八路配置。每个容器运行一个 `hw_server`，并映射一根 USB-JTAG 下载线。

## 准备

- Ubuntu 上已安装 Docker Engine 和 Docker Compose v2。Ubuntu 在虚拟机里运行时，把要使用的下载线直通给该虚拟机。
- 默认镜像为 `ghcr.io/wurunsong/vivado-lab:2018.3`，其中 Vivado Lab 装在 `/opt/Xilinx/Vivado_Lab/2018.3`。需要自行制作镜像时，从 AMD 获取 Linux Lab Edition 安装包。[AMD 2018.3 下载页](https://www.amd.com/en/support/downloads/adaptive-socs-and-fpgas/development-tools/2018-3.html)
- 用来连接的 Hardware Manager 同样使用 Vivado Lab 2018.3。

## 设置下载线

在 Ubuntu 上逐根接入下载线，用 `lsusb` 记录对应关系。例如 `Bus 002 Device 009` 对应 `/dev/bus/usb/002/009`。克隆仓库后复制 USB 路径模板。

```bash
git clone https://github.com/wurunsong/vivado-jtag-compose.git
cd vivado-jtag-compose
cp .env.example .env
```

在 `.env` 里为所选配置填写设备路径。同一次启动使用的下载线要填不同的路径。

## 拉取镜像

默认的 GHCR 镜像可匿名拉取，Compose 启动时会拉取本机缺少的镜像。也可以在 Ubuntu 上提前拉取。

```bash
sudo docker pull ghcr.io/wurunsong/vivado-lab:2018.3
```

已有 `.env` 时，将其中的 `VIVADO_IMAGE` 更新为 `ghcr.io/wurunsong/vivado-lab:2018.3`。如果要使用已有的本地镜像，可以设置 `VIVADO_IMAGE=vivado-lab:2018.3`。

## 启动与连接

| 配置文件 | 需要填写的变量 | 启动命令 |
| --- | --- | --- |
| `compose.yaml` | `JTAG_A` | `sudo docker compose up -d` |
| `compose-2-jtag.yaml` | `JTAG_A`、`JTAG_B` | `sudo docker compose -f compose-2-jtag.yaml up -d` |
| `compose-8-jtag.yaml` | `JTAG_A` 到 `JTAG_H` | `sudo docker compose -f compose-8-jtag.yaml up -d` |

更换配置后，如果要停止并移除上一套配置多出的容器，在新的启动命令末尾加 `--remove-orphans`。查看状态时使用与启动时相同的 `-f` 参数，将 `up -d` 换成 `ps`。

在 Ubuntu 的 Hardware Manager 里选择 **Open Target → Open New Target → Remote server**。主机填 `127.0.0.1`，`lab-a` 到 `lab-h` 的端口依次是 `13121` 到 `13128`。分别核对下载线序列号，再对相应板卡操作。

如果八路配置的 C 线重插后设备编号发生变化，更新 `.env` 的 `JTAG_C`。下面的命令会重建 C 路容器。

```bash
sudo docker compose -f compose-8-jtag.yaml up -d --force-recreate lab-c
```
