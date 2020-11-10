"""
应用: 多个actor 解析ip地址
Resolve a bunch of IP addresses using a pool of resolver actors.
"""

import pprint
import socket

from actor_model.chapter06.actor_register import ActorRegistry
from actor_model.chapter06.future import get_all
from actor_model.chapter06.threading import ThreadingActor


class Resolver(ThreadingActor):
    def resolve(self, ip):
        try:
            info = socket.gethostbyaddr(ip)
            print(f"Finished resolving {ip}")
            return info[0]
        except Exception:
            print(f"Failed resolving {ip}")
            return None


def run(pool_size, *ips):
    # Start resolvers 创建50个actor（其实就是50个线程）
    resolvers = [Resolver.start().proxy() for _ in range(pool_size)]

    # Distribute work by mapping IPs to resolvers (not blocking)
    hosts = []
    for i, ip in enumerate(ips):
        hosts.append(resolvers[i % len(resolvers)].resolve(ip))

    # Gather results (blocking) # 聚合结果
    ip_to_host = zip(ips, get_all(hosts))
    pprint.pprint(list(ip_to_host))

    # Clean up
    ActorRegistry.stop_all()


if __name__ == "__main__":
    ips = [f"193.35.52.{i}" for i in range(1, 50)]
    run(10, *ips)
