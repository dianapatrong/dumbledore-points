# Dumbledore Points

![Dumbledore](images/dumbledore.png)
House points are awarded to students at Hogwarts that do good deeds, correctly answer a question in class, 
or win a Quidditch Match. They can also be taken away for rule-breaking.

I created an Slack app where you can give points to your mates for taking time to help you out but also you can 
take them away. 

    "While you are at Hogwarts, your triumphs will earn your House points, while any rule-breaking will lose House points. 
    At the end of the year, the House with the most points is awarded the House Cup, a great honor. I hope each of you will be a credit to whichever 
    House becomes yours."
    -- Minerva McGonagall 

## Step-by-step
Originally I started to develop this app following the steps below, but since it was too tedious to copy the lambda function
each time to test I used **[AWS SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)**, this allowed
me to test locally, and to deploy it was really simple, AWS SAM packages and upload the deployment artifacts generated to an Amazon S3 bucket (created by AWS SAM CLI),
and then deploys the application using CloudFormation, so the only thing you need to create beforehand is the dynamoDB table.

### Step-1: Create a database
**AWS Console** -> **Services** -> **DynamoDB** -> **Create table**

* **Table name**: Hogwarts_Alumni
* **Primary Key**: username
* Click **Create**


### Step-2: Create a Lambda function
**AWS Console** -> **Services** -> **Lambda** -> **Create function**

* Select **Author from scratch**
* **Function name**: DumbledorePoints
* **Runtime**: Python 3.6
* **Create function**

> NOTE: Since I used AWS SAM, I did not have to copy my code directly into the AWS Lambda designer
> but if you don't want to do it with SAM you will need to create a zip package to upload it directly 
> or re-arrange the functions into a single file, for more inforrmation you can go to 
> [AWS Lambda deployment package in Python](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html).

#### Modify IAM Role
Within the function go to **Permissions** and click on the **Role name**, this will take you to **Identity and Access Management**

* Click on **Attach policies**
    - [x] AmazonDynamoDBFullAccess
    - [x] CloudWatchFullAccess

### Step-3: Create an API Gateway 
On the lambda function, click on **Add trigger**
* Select **API Gateway**
* Select **Create an API**
* **API Type**: REST API 
* Click **Add**

### Step-4: Slack integration
Go to `https://api.slack.com/apps` and click on **Create new app**

* **App Name**: Dumbledore Points
* **Development Slack Workspace**: < up 2 you >
* **Create App**

After creating the app select **Slash commands** -> **Create New Command**
* **Command**: /dumbledore
* **Request URL**: This will be the API Gateway url
* **Short description**: type "/dumbledore" to get the instructions
* Click **Save**

Under **Basic Information**, look for **Signing Secret**, go to the Lambda Function in the AWS Management Console
and add that as an environment variable
** **Name**: SLACK_KEY
** **Value**: < your secret > 


FOR MORE INFORMATION: 
* https://api.slack.com/authentication/verifying-requests-from-slack
* https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-hello-world.html


## How to use
There are different order that you can give with the same slash command `/dumbledore`, the first thing you need 
to do is to enroll to Hogwarts and to do so you can use the following commands: 

* `/dumbledore set house gryffindor` if you know which house you belong to
* `/dumbledore set house :sorting-hat:` if you want the sorting hat to take care of your house allocation

After you are enrolled you can either start giving or taking points away from your mates or you can optionally set a
title for yourself:

* `/dumbledore set title Diana Patron, Advisor to the Minister for Magic ` to set a cool title next to your name
* `/dumbledore give 10 points to @wizard1 @wizard2` or  `/dumbledore +10 @wizard1 @wizard2` to give points to 1 or more wizards
* `/dumbledore remove 10 points from @wizard1 @wizard2` or  `/dumbledore -10 @wizard1 @wizard2` to remove points from 1 or more wizards

To display the leaderboards:

* `/dumbledore leaderboard` will display the leaderboard for the four Hogwarts houses
* `/dumbledore gryffindor` will display the total of points of the house and the members leaderboard  

If you mess something up you will most likely end with a random message from dumbledore.

> **NOTE**: I used ![emojis](images/emojis) for the sorting hat feature and some of the responses