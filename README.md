# flask_writer
✍ A simple CMS for authors of web serials and blogs. 

This project is designed to be used as an author website for a writer of web serials, blogs, and/or novels. 

## Setup

### Install Requirements

To use it first install all packages in `/requirements.txt`:

```
# pip install -r requirements.txt
```

### Set Environment Variables

Next set the following environment variables, replacing the bracketed sections with data for your setup:

```
FLASK_APP=flask_writer.py
FLASK_ENV=[development or production]
MAIL_USERNAME=[]
MAIL_PASSWORD=[]
MAIL_DEFAULT_SENDER=[]
DATABASE_URI=[]
BASE_URL=[]
SITE_NAME=[]
```

See `/config.py` for a list of variables used.

### Add Starter Objects

```python
$ flask shell
>>> user = User(username=[YOUR USERNAME])
>>> user.set_password([YOUR PASSWORD])
>>> db.session.add(user)
>>> db.session.commit()
>>> admin_page = Page(title='Admin',slug='admin',user_id=user.id,sort=9999)
>>> admin_page.set_path()
>>> db.session.add(admin_page)
>>> db.session.commit()
>>> exit()
```

### Customization

The following files can be added to allow site-specific customization of the website. The first two files will need to be added in order to run the website. You can find example versions of the html files in `/app/templates/examples/`. Copy these into their correct directories to use the example files.

- **/app/templates/logo.html** - Required. Used for placing your logo in the navbar.
- **/app/templates/footer.html** - Required. Can be used for copyright or other information at the bottom of the page.
- **/app/templates/email/base-top.html** - Optional. Makes up the top half of the base of all emails.
- **/app/templates/email/base-bottom.html** - Optional. Makes up the bottom half of the base of all emails.
- **/app/static/css/custom.css** - Optional. For custom site-wide styling
- **/app/static/js/custom.js** - Optional. For custom site-wide javascript

### Run the App

Then run the app and access it at `localhost:5000/`:

```
flask run
```

### Special Pages

Some pages like the shop and search pages will not work unless you create them first through the admin panel. Creating them allows them to be used, and also gives you control over certain parts of the page. For these pages to work properly, they must have the specified slug as well as the `page` type. These pages **should not be published**, as that would make them show up in the site's navigation incorrectly. Below is a list of the required slugs and the ways you can affect each page's appearance.

- **admin** - You can change the Title, Banner, and Summary when editing this page.
- **search** - You can change the Title, Banner, and Summary.
- **shop** - You can change the Title Banner, and Summary. If you add a body, it will appear at the top of the page. This is the only special page that will need to be published to use. This allows you to also edit the sort order to determine where it falls in the navigation.
- **subscriber-welcome** - Used for emails. The title will be used as the subject and the body will be used as the text in the email. The banner also gets used as a background image for HTML emails. This email gets sent when someone subscribes to your site.
- **purchase-thank-you** - Used for emails in the same way as the subscriber-welcome page. This email is sent when someone purchases a downloadable product from your website.

