#importing necessary modules 
import discord 
from discord.ext import commands  
from github import Github              #for interacting with Github
from pymongo import MongoClient        #for interacting with MongoDB and storing data 
from mdutils.mdutils import MdUtils    #for generating the README.md file
import json                            #for parsing the config.json file and importing the private tokens

repo = None
readmeFile = None
mdFile = None
f = open('config.json')
tokens = json.load(f)
conn_string = tokens['mongo_connection_string']                # Connection string is needed for connecting to MongoDB
client = MongoClient(conn_string)                              # Logging in and initialising MongoDB client
db = client.dscrait                                            # Creating a collection of databases under 'dscrait'

def generateReadme():                                          # defining a function to generate the readme file 
    mdFile = MdUtils(file_name = "LOCAL_README.md")
    mdFile.new_header(level=1, title="Compilation Of DSC-RAIT resources")
    mdFile.new_paragraph("This is a compiled list of resources shared on the DSC-RAIT Discord Server!")
    for d in db.resources.find():                                                  
        '''
        db.resources.find() queries the database and returns all the data stored
        in the form of an iterable which contains all the domains and links present 
        under each domain, so we are looping through the iterable to insert each domain 
        and its respective resources in the readme file. Each element of the iterable
        is a python dictionary (in this case, it is 'd')
        {
            'domain': <domain name>, 
            'links': [
                {'info': <link-info1>,  'link': <link1>}, 
                {'info': <link-info2>,  'link': <link2>}, 
                ....
                ]
        } 
        ''' 
        mdFile.new_header(level = 2, title = d['domain'])
        for l in d['links']:                                                          
            mdFile.new_paragraph(text= f"{l['info']}: {l['link']}")
    mdFile.create_md_file()
    text = mdFile.read_md_file(file_name = "LOCAL_README.md")   # Read the created Readme file return its contents as a string
    return text
    
bot = commands.Bot(command_prefix = '!')               # Set our bot's command prefix as '!'

@bot.event
async def on_ready():                                        # Execute this function when the bot is online
    global repo, readmeFile, mdFile                    
    g = Github(tokens['github_token'])                       # Logging into Github and initialising the client
    repo = g.get_repo("dscrait/resources")                   # this is the repo we are going to modify the README.md of
    print('We have logged in as {0.user}'.format(bot))

@bot.command()
async def addDomains(ctx, *categories):                      #command for adding new domains to the Readme File.
    global repo, readmeFile, mdFile
    readmeFile = repo.get_contents("README.md")              
    for c in categories:
        db.resources.insert_one({                            #inserting the newly added domain/domains to the database
            'domain': c,
            'links': []
        })
    repo.update_file(readmeFile.path, "file update",  generateReadme(), readmeFile.sha)  
    await ctx.send(f'`{", ".join(categories)}` domains added successfully!')

@bot.command()
async def getDomains(ctx):                                   #command for getting the existing domains
    global repo
    domains = []
    for d in db.resources.find():                           
        domains.append(d['domain'])
    n = "\n-".join(domains)
    text = f"```Domains are:\n-{n}```"
    await ctx.send(text)

@bot.command()
async def add(ctx, domain, info, link):                      #command for adding new links to the respective domain
    global repo, readmeFile, mdFile
    readmeFile = repo.get_contents("README.md")
    db.resources.update_one({'domain': domain}, {'$addToSet': {'links': {'info': info, 'link': link}}})     #updating the 'links' field under each domain with a new link
    repo.update_file(readmeFile.path, "file update",  generateReadme(), readmeFile.sha)
    await ctx.send(f'Added under:{domain}')
    

bot.run(tokens['discord_token'])