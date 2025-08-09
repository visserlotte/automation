FROM public.ecr.aws/lambda/python:3.11

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LAMBDA_TASK_ROOT=/var/task \
    PYTHONPATH=/var/task

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ${LAMBDA_TASK_ROOT}

CMD ["handler.lambda_handler"]
