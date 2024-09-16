# Use an official Python runtime as a parent image
FROM public.ecr.aws/lambda/python:3.11

# Set the working directory to /var/task as expected by AWS Lambda
WORKDIR /var/task

# Copy the requirements file into the container at /var/task
COPY requirements.txt ./

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the src directory into /var/task/src
COPY src/ ./src

# Copy the main.py file directly into /var/task
COPY main.py .

# Set the default command to run the main.py script using Python
CMD ["main.lambda_handler"]
