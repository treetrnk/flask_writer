# flask_writer
✍ A simple CMS for authors of web serials and blogs. 

This project is designed to be used as an author website for a writer of web serials, blogs, and/or novels. 

To use it first install all packages in `/requirements.txt`:

```
# pip install -r requirements.txt
```

Next set the following environment variables, replacing the bracketed sections with data for your setup:

```
FLASK_APP=flask_writer.py
FLASK_ENV=[development or production]
MAIL_USERNAME=[]
MAIL_PASSWORD=[]
MAIL_DEFAULT_SENDER=[]
DATABASE_URI=[]
```

Then run the app and access it at `localhost:5000/`:

```
flask run
```
