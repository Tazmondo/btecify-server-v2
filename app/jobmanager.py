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
    coroutines: list[Coroutine]
    last_used: datetime
    progress: int = 0
    status: bool = False


jobs: dict[str, Job] = {}


async def coroutine_wrapper(coroutine: Coroutine, job: Job):
    try:
        result = await coroutine
    except Exception as e:
        result = e

    job.progress += 1
    job.last_used = datetime.now()
    if job.progress == job.size:
        job.status = True
    return result


# Takes a coroutine, runs it, and returns a job id which can be used to get its status.
async def start_job(coroutines: list[Coroutine]) -> str:
    newjobid = str(uuid())
    job = Job(
        job_id=newjobid,
        size=len(coroutines),
        coroutines=[],
        last_used=datetime.now()
    )
    job.coroutines = asyncio.gather(*[coroutine_wrapper(coroutine, job) for coroutine in coroutines])
    jobs[newjobid] = job
    return newjobid


def get_job(job_id: str):
    job = jobs.get(job_id)
    if job is not None:
        job.last_used = datetime.now()

    return job


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


    asyncio.run(entry())
