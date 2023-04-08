FROM python:3.10
COPY . ./app
WORKDIR app
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
