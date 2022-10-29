import asyncio
import openglider
import openglider.plots
import openglider.jsonify
import multiprocessing
from concurrent.futures import ProcessPoolExecutor


def unwrap(jsondata):
    patterns = openglider.jsonify.loads(jsondata)["data"]
    patterns.unwrap("/home/simon/oo")

pool = ProcessPoolExecutor(2)

async def main(loop):
    demo = openglider.load_demokite()
    p = openglider.plots.Patterns(demo)

    await loop.run_in_executor(pool, unwrap, openglider.jsonify.dumps(p))


_loop = asyncio.get_event_loop()
_loop.run_until_complete(main(_loop))