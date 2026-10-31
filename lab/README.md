# Linux Fundamentals lab

Ubuntu 26.04 LTS in a container, with **systemd as PID 1**, so `systemctl`, `journalctl`, cron and
timers all work. Free, and runs anywhere Podman or Docker runs (macOS, Windows, Linux).

## Start it
From the root of this repo:
```bash
podman build -t linux-lab lab/
podman run -d --name linux-lab --hostname linux-lab --cap-add=NET_RAW -p 8080:80 -p 9000:9000 linux-lab
podman exec -it -u devops -w /home/devops -e XDG_RUNTIME_DIR=/run/user/1000 linux-lab bash -l
```
User `devops` / password `devops`, in the `sudo` and `adm` groups. Stop with `podman stop linux-lab`; your
files stay until you `podman rm` it. Tested with Podman; Podman runs systemd containers out of the box.

Then clone this repo again **inside** the lab (`git clone https://github.com/david-wagih/FlowApprove.git`)
and work there.

## Good to know
- `ls -l` shows a `+` after the permissions (`-rw-r--r--+`). That's the SELinux labels Podman's VM
  puts on every file, not an ACL you set. A normal server doesn't show it
- `/proc`, `df`, `free` and `uptime` show the VM Podman runs in, not your own machine
- `ip a` shows the container's network (10.88.x.x). To reach it from your machine, you need the `-p` ports above
- For timers, use `OnCalendar=`. `OnUnitActiveSec=` doesn't reschedule reliably in a container
- Ubuntu 26.04 ships Rust coreutils (uutils), so some error messages differ from older tutorials
