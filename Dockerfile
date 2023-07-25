# docker build -t starlette-admin-image .
# docker run --name starlette-admin-container starlette-admin-image
# docker rm starlette-admin-container
# docker rmi starlette-admin-image

FROM python:3.7

COPY . /app/starlette-admin
WORKDIR /app/starlette-admin

# install git
RUN apt-get update && \
    apt-get install -y --no-install-recommends git

# install hatch
RUN pip install hatch

# clone app, branch 'beanie-support'
# RUN git clone -b beanie-support https://github.com/opaniagu/starlette-admin.git

WORKDIR /app/starlette-admin

# run test
CMD ["hatch", "-e", "test", "run", "-m", "pytest", "-v", "tests/beanie"]
