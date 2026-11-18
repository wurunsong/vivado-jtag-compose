from fcntl import LOCK_EX, flock
from pathlib import Path


def parse_hosts(contents):
    aliases = {}
    for line in contents.splitlines():
        fields = line.partition("#")[0].split()
        for hostname in fields[1:]:
            aliases.setdefault(hostname.lower(), set()).add(fields[0])
    return aliases


def install_aliases(config_path, hosts_path):
    desired = parse_hosts(config_path.read_text(encoding="utf-8"))
    with hosts_path.open("r+", encoding="utf-8", errors="surrogateescape") as hosts_file:
        flock(hosts_file, LOCK_EX)
        contents = hosts_file.read()
        existing = parse_hosts(contents)
        additions = []

        for hostname, addresses in desired.items():
            current = existing.get(hostname, set())
            conflicts = current - addresses
            if conflicts:
                conflicting_addresses = ", ".join(sorted(conflicts))
                raise SystemExit(
                    f"{hostname} 已映射到 {conflicting_addresses}，请检查 {hosts_path}。"
                )
            for address in sorted(addresses - current):
                additions.append(f"{address} {hostname}")

        if additions:
            separator = "\n" if contents and not contents.endswith("\n") else ""
            hosts_file.write(separator + "\n".join(additions) + "\n")
        return len(additions)


if __name__ == "__main__":
    config_path = Path(__file__).resolve().with_name("hosts.example")
    count = install_aliases(config_path, Path("/etc/hosts"))
    print(f"新增 {count} 个 Vivado 主机名别名。")
