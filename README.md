## vapordrive

To get started with development:

Create a new virtualenv for this project

    virtualenv ~/vapordrive-env
    source ~/vapordrive-env/bin/activate

Install the requirements

    pip install -r requirements.txt

Setup the S3 env vars by adding to ``~/.bash_profile``

    export AWS_ACCESS_KEY=xxxx
    export AWS_SECRET_KEY=xxxx
