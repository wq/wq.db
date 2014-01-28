from rest_framework.response import Response
from rest_framework.decorators import link, action
from wq.db.rest.views import ModelViewSet
from wq.db.contrib.dbio import tasks
from wq.db.rest import app
from celery.result import AsyncResult

import swapper
File = swapper.load_model('files', 'File')


class FileViewSet(ModelViewSet):
    cached = False

    @link()
    def status(self, request, *args, **kwargs):
        taskid = request.GET.get('task', None)
        if not taskid:
            return Response({})

        result = AsyncResult(taskid)
        response = {
            'status': result.state
        }
        if result.state in ('PROGRESS', 'SUCCESS'):
            response.update(result.result)
        elif result.state == 'FAILURE':
            response['error'] = repr(result.result)
        return Response(response)

    def run_task(self, name, async=False):
        response = self.retrieve(self.request, **self.kwargs)
        task = getattr(tasks, name).delay(self.object, self.request.user)
        if async:
            response.data['task_id'] = task.task_id
        else:
            response.data['result'] = task.get()
        return response

    @link()
    def start(self, request, *args, **kwargs):
        self.action = 'columns'
        return self.run_task('read_columns')

    @action()
    def columns(self, request, *args, **kwargs):
        response = self.run_task('read_columns')
        result = tasks.update_columns.delay(
            self.object, request.user, request.POST
        )
        response.data['result'] = result.get()
        return response

    @action()
    def reset(self, request, *args, **kwargs):
        self.task = 'retrieve'
        response = self.run_task('reset')
        return response

    @action()
    def data(self, request, *args, **kwargs):
        return self.run_task('import_data', async=True)

app.router.register_model(File, viewset=FileViewSet)
