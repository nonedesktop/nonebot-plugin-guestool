import asyncio
from contextlib import suppress
from ipaddress import AddressValueError, IPv4Address, IPv6Address
import click
import server

def addr_validate(ctx, param, value) -> IPv4Address | IPv6Address:
    with suppress(AddressValueError):
        return IPv4Address(value)
    with suppress(AddressValueError):
        return IPv6Address(value)
    raise click.BadParameter(f"{value!r} is not an IPv4 or IPv6 address", ctx, param)


@click.command()
@click.option("--host", "-H", nargs=1, default="127.0.0.1", callback=addr_validate)
@click.option("--port", "-P", nargs=1, default=37103, type=click.IntRange(1, 65535))
def main(host: IPv4Address | IPv6Address, port: int):
    print(f"[HOST] Running test host server at {host=}, {port=}")
    asyncio.run(server.run(str(host), port))


if __name__ == "__main__":
    main()