import asyncio
import argparse
from hypercorn.asyncio import serve
from hypercorn.config import Config as HypercornConfig
from app import app

def parse_args():
    parser = argparse.ArgumentParser(description="Run Quart app with Hypercorn")
    parser.add_argument("-b", "--bind", default="0.0.0.0", 
                        help="Bind address (default: 0.0.0.0)")
    parser.add_argument("-p", "--port", type=int, default=1337, 
                        help="Port to bind (default: 1337)")
    parser.add_argument("-c", "--certfile", 
                        help="Path to SSL certificate file (optional)")
    parser.add_argument("-k", "--keyfile", 
                        help="Path to SSL key file (optional)")
    return parser.parse_args()

async def main():
    args = parse_args()

    config = HypercornConfig()
    config.bind = [f"{args.bind}:{args.port}"]
    config.workers = 1
    # note: you should only use 1 worker unless you want some fun and random 
    # surprises - all of the stats for the game are stored in memory, each 
    # worker has its own memory space. If you get assigned to a different 
    # worker, you'll have a different set of objective progress, chat 
    # histories, etc...

    # TLS if hosted on the web
    if args.certfile and args.keyfile:
        config.certfile = args.certfile
        config.keyfile = args.keyfile

    await serve(app, config)

if __name__ == "__main__":
    asyncio.run(main())
