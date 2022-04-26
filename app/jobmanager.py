import uuid

@dataclass
class Job():
    job_id: str
    coroutine

jobs = {}

# Takes a coroutine, runs it, and returns a job id which can be used to get its status.
def startJob(coroutine) -> str:
    newjobid = uuid()
    

