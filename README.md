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

## wishlist

- ~~Multi-part uploads and retries for large files that fail with broken pipe and connection reset~~
- Mechanism to re-download file when moved out of vapordrive folder or when opened.
- Get rid of ".remote" extensions
- Move keys to a server API that responds with signed requests user is allowed to make.
