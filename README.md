# Vivado Lab JTAG 容器配置

在 x86-64 Ubuntu 上运行 Vivado Lab 2018.3。默认配置启动一个容器，也可以选择两路或八路配置。每个容器运行一个 `hw_server`，并映射一根 USB-JTAG 下载线。

## 准备

- x86-64 Ubuntu 上已安装 Docker Engine、Docker Compose v2 和 `usbutils`。Ubuntu 在虚拟机里运行时，把要使用的下载线直通给该虚拟机。[Docker Engine 安装文档](https://docs.docker.com/engine/install/ubuntu/)
- 用来连接的 Hardware Manager 同样使用 Vivado Lab 2018.3。

## 制作本地镜像

打开 AMD 下载页，在 **Vivado Lab Solutions – 2018.3** 下选择 **Vivado 2018.3: Lab Edition - Linux**（593.81 MB）。按下载页提示登录，将安装包保存到运行 Docker 的 Ubuntu。安装包的原始文件名为 `Xilinx_Vivado_Lab_Lin_2018.3_1207_2324.tar.gz`。[AMD 2018.3 下载页](https://www.amd.com/en/support/downloads/adaptive-socs-and-fpgas/development-tools/2018-3.html)

1. 在 Ubuntu 终端拉取 `linux/amd64` 的 Ubuntu 18.04 基础镜像，然后启动临时容器。将 `archive` 改成安装包的实际绝对路径。Ubuntu 18.04 是镜像里的运行环境，虚拟机可以使用 Ubuntu 24.04。[Vivado 2018.3 安装指南](https://docs.amd.com/v/u/2018.3-English/ug973-vivado-release-notes-install-license)

   ```bash
   sudo docker pull --platform linux/amd64 ubuntu:18.04

   archive='/实际路径/Xilinx_Vivado_Lab_Lin_2018.3_1207_2324.tar.gz'
   test -f "$archive" && sudo docker run --pull=never --platform linux/amd64 \
     -it --name lab183-build \
     --mount "type=bind,source=$archive,target=/tmp/vivado-lab.tar.gz,readonly" \
     ubuntu:18.04 bash
   ```

   已用 `docker load` 导入 amd64 基础镜像时，可以从 `archive=...` 开始。临时容器中途退出后，可用 `sudo docker start -ai lab183-build` 继续。

2. 在临时容器里的终端安装依赖、解压安装包并生成配置。如果 `ConfigGen` 显示选项，选择 **Vivado Lab Edition**。记下它打印的配置文件路径。

   ```bash
   apt-get update && apt-get install -y --no-install-recommends \
     ca-certificates libtinfo5 libncurses5 libudev1 \
     libusb-1.0-0 libusb-0.1-4 \
     libx11-6 libxext6 libxrender1 libxtst6 libxi6 \
     libsm6 libxrandr2 libxft2 libfontconfig1 fonts-dejavu-core

   mkdir -p /tmp/lab
   tar -xzf /tmp/vivado-lab.tar.gz -C /tmp/lab --strip-components=1
   cd /tmp/lab
   ./xsetup -b ConfigGen
   ```

3. 仍在临时容器里，将 `cfg` 设为安装器打印的完整路径。阅悉并同意安装条款后执行以下命令。安装目标必须为 `/opt/Xilinx`，Compose 会从该目录加载 Vivado 2018.3 的环境脚本。[Vivado 2018.3 批量安装说明](https://docs.amd.com/api/khub/documents/4ahtxBp53qH38bUxWqDd0A/content#page=41)

   ```bash
   cfg=/root/.Xilinx/install_config.txt
   ls -l "$cfg" &&
     sed -i 's|^Destination=.*|Destination=/opt/Xilinx|' "$cfg" &&
     grep -Fx 'Destination=/opt/Xilinx' "$cfg" &&
     ./xsetup --agree XilinxEULA,3rdPartyEULA,WebTalkTerms \
       --batch Install --config "$cfg" &&
     ls -l /opt/Xilinx/Vivado_Lab/2018.3/settings64.sh \
       /opt/Xilinx/Vivado_Lab/2018.3/bin/{vivado_lab,hw_server}
   ```

4. 确认上一步成功后，清理容器里的解压目录并退出。

   ```bash
   cd /
   rm -rf /tmp/lab
   exit
   ```

5. 回到 Ubuntu 终端，将已安装的容器保存为 Compose 使用的镜像 `vivado-lab:2018.3`。`docker commit` 写入镜像时可能要等几分钟，完成后会打印镜像 ID。

   ```bash
   sudo docker commit lab183-build vivado-lab:2018.3
   sudo docker image ls vivado-lab:2018.3
   ```

6. 用 Tcl 模式验证容器能启动 Vivado Lab。看到 `Vivado Lab v2018.3` 和 Tcl 提示符后，输入 `exit` 退出。

   ```bash
   sudo docker run --pull=never --rm -it vivado-lab:2018.3 \
     bash -c 'source /opt/Xilinx/Vivado_Lab/2018.3/settings64.sh && exec vivado_lab -mode tcl'
   ```

## 设置下载线

在 Ubuntu 上逐根接入下载线，用 `lsusb` 记录对应关系。例如 `Bus 002 Device 009` 对应 `/dev/bus/usb/002/009`。克隆仓库后复制 USB 路径模板。

```bash
git clone https://github.com/wurunsong/vivado-jtag-compose.git
cd vivado-jtag-compose
cp .env.example .env
```

在 `.env` 里为所选配置填写设备路径。同一次启动使用的下载线要填不同的路径。已有 `.env` 时，确认其中的 `VIVADO_IMAGE` 为 `vivado-lab:2018.3`，或者删除这一行使用默认值。Compose 使用本地镜像，启动前确认镜像已制作完成。

## 启动与连接

| 配置文件 | 需要填写的变量 | 启动命令 |
| --- | --- | --- |
| `compose.yaml` | `JTAG_A` | `sudo docker compose up -d` |
| `compose-2-jtag.yaml` | `JTAG_A`、`JTAG_B` | `sudo docker compose -f compose-2-jtag.yaml up -d` |
| `compose-8-jtag.yaml` | `JTAG_A` 到 `JTAG_H` | `sudo docker compose -f compose-8-jtag.yaml up -d` |

更换配置后，如果要停止并移除上一套配置多出的容器，在新的启动命令末尾加 `--remove-orphans`。查看状态时使用与启动时相同的 `-f` 参数，将 `up -d` 换成 `ps`。

在 Ubuntu 的 Hardware Manager 里选择 **Open Target → Open New Target → Remote server**。主机填 `127.0.0.1`，`lab-a` 到 `lab-h` 的端口依次是 `13121` 到 `13128`。在 Hardware Targets 列表确认相应下载线。多根线报告相同序列号时，可以按端口和 `.env` 中映射的 USB 节点区分。

如果八路配置的 C 线重插后设备编号发生变化，更新 `.env` 的 `JTAG_C`。下面的命令会重建 C 路容器。

```bash
sudo docker compose -f compose-8-jtag.yaml up -d --force-recreate lab-c
```

### 配置主机名别名

`hosts.example` 提供 `vivado-a` 到 `vivado-h` 八个别名。它们都解析到 `127.0.0.1`。在 Docker 所在的 Ubuntu 上运行 Hardware Manager 时，从仓库目录执行：

```bash
sudo python3 install-hostnames.py
getent -s files hosts vivado-a vivado-b
```

安装命令将缺少的别名追加到 `/etc/hosts`。已有同名记录指向其他 IP 时，命令会提示冲突，可以用 `sudoedit /etc/hosts` 核对。

在 **Remote server** 向导中分别填写主机名和端口。单路用 A，两路用 A 和 B，八路用表中全部配置。

| Compose 服务 | Host name | Port |
| --- | --- | --- |
| `lab-a` | `vivado-a` | `13121` |
| `lab-b` | `vivado-b` | `13122` |
| `lab-c` | `vivado-c` | `13123` |
| `lab-d` | `vivado-d` | `13124` |
| `lab-e` | `vivado-e` | `13125` |
| `lab-f` | `vivado-f` | `13126` |
| `lab-g` | `vivado-g` | `13127` |
| `lab-h` | `vivado-h` | `13128` |

在 Vivado Lab 2018.3 的实测环境中，一个会话只能连接一个 `hw_server`。要同时使用多个容器，可以为每路启动一个独立的 Vivado Lab 实例。
