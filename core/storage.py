class Storage:
    def __init__(self):
        self.tasks = {}

    async def save_task(self, job_id: str, data: dict):
        self.tasks[job_id] = data

    async def get_task(self, job_id: str):
        return self.tasks.get(job_id)

storage = Storage()