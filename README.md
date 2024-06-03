# News_Harbor
News Harbor is modern media site, powered by AI aricle generations.

Visit website:

http://dawidlycz2.pythonanywhere.com/

## About the App
News Harbor is a web application built on the Django framework, allowing users to browse articles about various topics. Modern design imporoves user expirience. Additionally, the application has possibility to generate article about any topic by simply providing it in one text field.

### Key Features:
* News Browsing: News Harbor is media website, therefore it provides possibility to read various articles about any topic.

* Feedback System: Website allows logged users to leave a like, or even a comment regarding specific article, so they might express their sentiment about article. Comment system also allows to leave a like or dislike to specific comment.

* Article and Image divide: One of adventages of News Harbor is division of articles and images in database. This means one article might have assigned many images, and one image might be assigned to many articles. This provides flexibility for creators.

* Tag System: Every article and every image has assigned many tags, which makes it easer to find, simply by searching it, in searchfield.

* Editor Panel: This feature might be only for editors, but its worth of mentioning. Website has modern editor panel, that probides possibility to create, edit, and delete articles, images, and tags in comfortable way.

* User-Friendly Interface: The app features a user-friendly interface. The intuitive design ensures seamless navigation through the wealth of available information.

* AI Article Generation: Main feature of News Harbor is possibility to generate articles with help of artificial inteligence. In editors panel, mentioned before, there is possibility to provide a topic, and send request to AI endpoint, which returns article. Next, article is formatted by script, so it fits perfectly to a database.

* API: Application has API. More information about it, directly in website.
## Become an Editor:

<img src="tutorial_images/tutorial1.png" alt="Tutorial Image1" width="800" height="600">


## Dependencies

The project relies on the following Python libraries and packages:

- [mysqlclient](https://pypi.org/project/mysqlclient/): A MySQL database connector for Django.
- [Django Rest Framework](https://www.django-rest-framework.org): A tool to create and use API.
Make sure to install these dependencies by running the following command:

```bash
pip install -r requirements.txt
