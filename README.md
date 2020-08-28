# Dumbledore Points

![Dumbledore](images/dumbledore.png)
House points are awarded to students at Hogwarts that do good deeds, correctly answer a question in class, 
or win a Quidditch Match. They can also be taken away for rule-breaking.

With this tutorial we will create an Slack app where you can give points to your mates for taking time to help you out but also you can 
take them away. 

    _"While you are at Hogwarts, your triumphs will earn your House points, while any rule-breaking will lose House points. 
    At the end of the year, the House with the most points is awarded the House Cup, a great honor. I hope each of you will be a credit to whichever 
    House becomes yours."_
    -- Minerva McGonagall 

## Step-by-step
Originally I started to develop this app following the steps below, but since it was too tedious to copy the lambda function
each time I used **AWS SAM**. 

## Step-1: Create a database
**AWS Console** -> **Services** -> **DynamoDB** -> **Create table**

* **Table name**: DumbledorePoints
* **Primary Key**: username
* Click **Create**


## Step-2: Create a Lambda function
**AWS Console** -> **Services** -> **Lambda** -> **Create function**

* Select **Author from scratch**
* **Function name**: DumbledorePoints
* **Runtime**: Python 3.6
* **Create function**

#### Modify IAM Role
Within the function go to **Permissions** and click on the **Role name**, this will take you to **Identity and Access Management**

* Click on **Attach policies**
    - [x] AmazonDynamoDBFullAccess
    - [x] CloudWatchFullAccess

## Step-3: Create an API Gateway 
On the lambda function, click on **Add trigger**
* Select **API Gateway**
* Select **Create an API**
* **API Type**: REST API 
* Click **Add**

## Step-4: Slack integration
Go to `https://api.slack.com/apps` and click on **Create new app**

* **App Name**: Dumbledore Points
* **Development Slack Workspace**: < up 2 you >
* **Create App**

After creating the app select **Slash commands** -> **Create New Command**

Under **Basic Information**, look for **Signing Secret**, go to the Lambda Function
and add that as an environment variable
** **Name**: SLACK_KEY
** **Value**: < your secret > 


FOR MORE INFORMATION: 
* https://api.slack.com/authentication/verifying-requests-from-slack
* https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-hello-world.html