import picadios.picadiosMain
import asyncio

main = picadios.picadiosMain.PicadiosMain()

loop = asyncio.get_event_loop()
loop.run_until_complete(main.start())
loop.run_forever()