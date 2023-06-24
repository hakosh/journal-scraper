from aiohttp import ServerDisconnectedError


def retry(count=3):
    def decorator(fn):

        async def wrapper(*args, **kwargs):
            attempt = 0

            while True:
                if attempt:
                    print(f'trying - attempt #{attempt}')

                try:
                    return await fn(*args, **kwargs)
                except ServerDisconnectedError as error:
                    print(f'caught error: {type(error).__name__} {error}')
                    attempt += 1

                    if attempt == count:
                        print(f'failed after {attempt} attempts')
                        raise error
                    else:
                        continue

        return wrapper

    return decorator
