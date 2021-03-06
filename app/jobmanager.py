import asyncio
from dataclasses import dataclass
from datetime import datetime
from random import randint
from typing import Coroutine
from uuid import uuid4 as uuid


@dataclass
class Job:
    job_id: str
    size: int
    coroutines: list[asyncio.Future]
    last_used: datetime
    progress: int = 0
    status: bool = False


jobs: dict[str, Job] = {}


async def coroutine_wrapper(coroutine: Coroutine, job: Job, on_finish: Coroutine):
    try:
        result = await coroutine
    except Exception as e:
        result = e

    job.progress += 1
    job.last_used = datetime.now()
    if job.progress == job.size:
        job.status = True
        await on_finish
    return result


# Takes a coroutine, runs it, and returns a job id which can be used to get its status.
async def start_job(coroutines: list[Coroutine], on_finish: Coroutine = None) -> str:
    newjobid = str(uuid())
    job = Job(
        job_id=newjobid,
        size=len(coroutines),
        coroutines=[],
        last_used=datetime.now(),
        status=(len(coroutines) == 0)  # if number of coroutines is 0 it isn't infinitely stuck on false
    )
    coroutines_to_await = [coroutine_wrapper(coroutine, job, on_finish) for coroutine in coroutines]
    job.coroutines = asyncio.gather(*coroutines_to_await)
    if len(coroutines_to_await) == 0:
        await on_finish
    jobs[newjobid] = job
    return newjobid


def get_job(job_id: str):
    job = jobs.get(job_id)
    if job is not None:
        job.last_used = datetime.now()

    return job


def delete_job(job_id):
    job = jobs.get(job_id)
    if job:
        for job_task in job.coroutines:  # Cancel job's current tasks.
            job_task.cancel()

        del jobs[job.job_id]

        return True
    return False


if __name__ == "__main__":
    async def myFunction(time):
        print("Sleeping for " + str(time))
        await asyncio.sleep(time)
        return time


    async def entry():
        jobid = await start_job([myFunction(randint(100, 600) / 100) for i in range(20)])
        job = jobs[jobid]
        prevprogress = -1
        prevtime = datetime.now()
        while job.progress != job.size:
            if job.progress != prevprogress:
                print(job.progress)
                prevprogress = job.progress
            await asyncio.sleep(0.1)

        timetaken = datetime.now() - prevtime
        print(timetaken, job)


    async def entry2():
        async def done():
            print("lol")

        async def awaiter(thing):
            await thing

        await awaiter(done())


    asyncio.run(entry())
