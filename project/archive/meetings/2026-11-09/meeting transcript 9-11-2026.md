00:00:01 Speaker 1
Okay,

00:00:02 Speaker 1
Great. Does everyone have a chance to take a look at the notes?

00:00:10 Speaker 1
What I said in the group chat is about EV one.

00:00:16 Speaker 1
Yeah.

00:00:24 Speaker 1
These are the data that I've collected. Let me show it in a nicer way.

00:00:33 Speaker 1
So all I did was plan out what data we're gonna need and when we are optimizing for EV charging stations around Singapore. The data we're gonna need is the current supply of EV charging, the current amount of EV cars on the road and the future demand of EV cars on the road.

00:01:00 Speaker 1
Then I take a deeper dive into

00:01:04 Speaker 1
What are

00:01:06 Speaker 1
How much can each of the EV charger supply

00:01:10 Speaker 1
To relative to each car? Where are they distributed?

00:01:15 Speaker 1
So I go from that angle, and then what I eventually want to figure out is not only how many chargers we're going to need

00:01:23 Speaker 1
But also where to place them, because I think that will be a very interesting sharing that when we share with the professor, then we go from the angle that we know that this is how the EV charger should be allocated, but we also think one step ahead about how it is going to change over the years, because the demand doesn't increase overnight.

00:01:47 Speaker 1
So how should we plan over the years on how to adjust and where should we place these EV chargers over the years?

00:01:56 Speaker 1
In order to create that insight

00:02:00 Speaker 1
This is all the documents that I prepared.

00:02:03 Speaker 1
What I share in the GitHub link, you guys can go ahead and take a look at. All of these are real data. All of them are LTA from LTA HDBs and URA.

00:02:17 Speaker 1
Feel free to take a look at it. And I think today what we want to talk about is just to align that. Whether this angle is good enough. Whether we want to change something in this narrative, and the next step

00:02:31 Speaker 1
A lot of the analytics work, a lot of the data consolidation, ETL kind of work, I'll leave it to the agent. But mostly it's whether this point of view, whether this narrative is going to

00:02:44 Speaker 1
It's you.

00:02:46 Speaker 1
What does everybody think about this narrative, and whether we should adjust it for the presentation.

00:02:54 Speaker 2
There's no presentation.

00:02:55 Speaker 1
No presentation.

00:03:00 Speaker 1
Yeah.

00:03:01 Speaker 2
Yeah,

00:03:03 Speaker 2
It's just a report.

00:03:05 Speaker 2
And other than the presentation on Wednesday, I don't think I'm going to class anymore.

00:03:08 Speaker 3
Yeah.

00:03:11 Speaker 3
Oh wait, there's no more.

00:03:13 Speaker 1
There's no more classes.

00:03:15 Speaker 2
Bro, what the hell are you doing?

00:03:18 Speaker 3
I know Wednesday there's a class.

00:03:19 Speaker 1
But Friday is there a class?

00:03:21 Speaker 2
I think there is actually.

00:03:22 Speaker 3
I think that's the term. It's just that you don't have to go since there's nothing else.

00:03:30 Speaker 1
I don't. Cool, nice.

00:03:33 Speaker 3
Good news.

00:03:36 Speaker 2
Just in case, if you don't know, next week there's no more classes. Just in case you go to class and there's nobody here.

00:03:43 Speaker 2
No.

00:03:44 Speaker 1
Next week our presentation.

00:03:46 Speaker 2
This week.

00:03:47 Speaker 3
This week

00:03:49 Speaker 2
So this week is the last week.

00:03:54 Speaker 3
All right

00:03:58 Speaker 4
Can I check for estimating the demand? The demand part. You mentioned one more part we wanted to do is how the demand grows over the years.

00:04:09 Speaker 4
Do you need the data because you have a data set on Population by planning area?

00:04:17 Speaker 4
The census twenty twenty one.

00:04:19 Speaker 4
Would you need historical data for that?

00:04:22 Speaker 4
Yes. To measure the growth rates.

00:04:25 Speaker 1
Who many charging where contacts?

00:04:34 Speaker 1
Ah.

00:04:36 Speaker 1
Demand should be here. Let me take a look at what we have. I'm asking to fetch anything that's relatively usable. To be fair, it doesn't mention that it doesn't have the data. Something like, where are the EVs parking right now? Those data LTA doesn't have, Singapore doesn't have.

00:04:59 Speaker 4
But where are the EVs parking? They don't. It could be just at the end of the HDB parking lots, right?

00:05:08 Speaker 1
One way we can go around this is by getting the HDB data about how many cars are parking in each area of Singapore.

00:05:20 Speaker 4
You need the exact number at each parking?

00:05:24 Speaker 4
Can we just not proxy by the number of parking lots?

00:05:28 Speaker 1
That also works. That also works. So what I want to do is just to have like a proxy number for that.

00:05:40 Speaker 4
Because I was looking at the census twenty twenty dataset for the number of persons by area.

00:05:47 Speaker 4
Then if you need the his if you need time series, then you can also use. There's another one for twenty twenty five.

00:05:54 Speaker 4
So you can plug that in as well if you need to.

00:05:58 Speaker 1
Okay.

00:06:00 Speaker 1
Twenty twenty.

00:06:00 Speaker 4
That one will be under the general household survey. Twenty twenty five.

00:06:04 Speaker 1
Would you mind sharing that link?

00:06:06 Speaker 4
Can I share a little?

00:06:15 Speaker 1
By the way, I actually took a look at the requirement. We are submitting a final report. What are the requirements of that report?

00:06:30 Speaker 3
I think there are a few requirements we need to meet.

00:06:37 Speaker 3
The one that we are.

00:06:39 Speaker 2
Sorry. It's actually very like.

00:06:42 Speaker 2
Free for all kind of thing, they don't have much requirements besides the fact that there's no page limitation. It just says that excluding appendices must be eight to fourteen pages, but then eight to fourteen pages is like one inch margins.

00:07:00 Speaker 2
Time font size trough, and it's double space. So double space means that it's a lot more.

00:07:08 Speaker 2
I mean the spacing is a lot wider, so it's probably not as much as we think.

00:07:12 Speaker 1
I see.

00:07:13 Speaker 4
Oh my god, you have a Google Docs, right? I think yeah

00:07:16 Speaker 2
It's in the Google Docs. The guideline.

00:07:18 Speaker 1
Google Docs. Is it somewhere here as well?

00:07:22 Speaker 2
The one. Let me just send it a check again.

00:07:25 Speaker 3
The thing we are missing currently is that they want our model to reference a known model.

00:07:33 Speaker 3
And do citation about the model, like what model is this, where is it research from. Why do we use the model to estimate this? I think we need to find a few references about

00:07:44 Speaker 3
And define our model called facility location model.

00:07:48 Speaker 4
Then, yes

00:07:49 Speaker 3
Then we can. I think, 

00:07:51 Speaker 4
I've indicated something like that in the Google Docs.

00:07:55 Speaker 2
You can take a look at the evaluation of the project. That's like the, but they don't have like specifically what must be done. It's more like.

00:08:05 Speaker 2
Must explain this. Must explain that. You must cite references.

00:08:10 Speaker 1
Brah, I'm reading all that.

00:08:14 Speaker 3
And that's crazy. Is it generated with AI?

00:08:17 Speaker 1
It doesn't seem like it's generated with AI.

00:08:19 Speaker 2
Is it? It's just nonsense.

00:08:21 Speaker 2
It's just nonsense.

00:08:23 Speaker 3
I think this is his guideline for the past ten years. It's just the same thing.

00:08:28 Speaker 1
That's why it's like with all the red lines underneath it.

00:08:35 Speaker 3
Like parents.

00:08:38 Speaker 3
I don't have a question, so I didn't dive into the CSD file, but I pipe it into my AI. Then there is this part about wait let me see. So we don't have the private as the estimate for the EV in the private places. We only have the announcement saying that they will be this number. But the public one is this number, so there's this gap.

00:09:07 Speaker 3
I think we might need to.

00:09:10 Speaker 3
I think it's justifiable.

00:09:13 Speaker 3
So the twenty three k private points, I managed to run some justification on a CSP saying that based on the public announcement is for example forty k

00:09:25 Speaker 3
But in the private, in the public data is twenty k, so there's a gap.

00:09:29 Speaker 3
And then they estimated about one third of the public share is private. So it mentions that I think we. My question is: Do we want to use the public LTA data to do this model, or do we want to use the public plus private data to estimate

00:09:48 Speaker 3
Which charging point to put across private and public, or only focusing on public?

00:09:56 Speaker 4
I think we can focus on public.

00:09:58 Speaker 2
I also think it's better to focus on public.

00:10:00 Speaker 3
Because for private.

00:10:03 Speaker 4
So it's more like a policy demand. We don't have the data firstly, and it's more like we can go by a policy angle where the government can indicate where to place the EV chargers. Because for private estates, they need to go through your private MCS T and all that. So the government may also not be able to.

00:10:20 Speaker 2
For private estate, right? It's not paid by the government, so the private estates have to agree that they want to build more, and then they come up with money within the estate. It is a totally different policy, and even if the government says a certain policy, right, they don't have to follow it either. We just follow using the angle, which is probably easier to justify.

00:10:41 Speaker 3
Also, the angle will definitely be where to put the charging port in public places

00:10:49 Speaker 4
In the HDB places.

00:10:51 Speaker 3
I think maybe HDB park, about we can define that a bit tighter using whatever data Regan has here. I think it's very comprehensive.

00:11:00 Speaker 3
Then another one, I think, you also have a bit. We need to confirm that is

00:11:06 Speaker 3
I think the proposal to do this model is to predict where we should put it. Firstly, where should we put it

00:11:14 Speaker 3
The charging port at the minimum cost.

00:11:18 Speaker 3
One part is that for the slow charging model, I think basically because each calculation was by cost per area. So basically, the model might simply just say, 'Oh, there's some car here. Let's put a slow charging.' So it might not be that we need an optimization model to do that. So maybe that part we can just briefly walk through. I think the interesting part will be the fast charging hubs because it's more costly.

00:11:51 Speaker 3
So a lot of our report should be focusing on where we should park the fast charging hubs instead of focusing on the slow one.

00:12:01 Speaker 1
That's the other part. I think during the class, they talk a lot about optimization based on each of the let's say the charging port cost, and also the price, like the reward is gonna yield. So how do we maximize that?

00:12:24 Speaker 1
Those figures are here.

00:12:27 Speaker 1
But I also.

00:12:30 Speaker 1
That this can also be the second part of the optimization problem.

00:12:34 Speaker 1
Which is while we are optimizing, where do we put these chargers? Obviously the more the better. We might also want to set a limit on

00:12:42 Speaker 1
An assumption about how much fund is allocated to create these chargers, and based on each level of fund

00:12:51 Speaker 1
The location and the type of chargers that we put could be different.

00:12:59 Speaker 3
But we don't have the numbers for the estimated funds.

00:13:05 Speaker 1
That's the complicated part.

00:13:08 Speaker 4
We can come up with a better solution.

00:13:12 Speaker 3
So I think that's why when I was talking to my AI, it was like because we don't have the number, and then the model might just give a very obvious answer saying that oh, let's just put a slow charging cup port in.

00:13:26 Speaker 3
Big car park like if the car park is big enough, we just put one in there because this is how we define our model. That might be the actual case we should do for every car park. If there's a car park which is big enough, there's definitely a need for EV charging, so we just put a slow one. I think that makes sense. It's a no-brainer. Just the fast charging one will be the strategic one. I was just thinking, maybe our report should focus a lot more on the fast charging one.

00:13:57 Speaker 3
And don't have to hop on the slow one because it might just be an obvious answer that we cannot solve.

00:14:04 Speaker 1
I would suggest either pick a fast charger or a slow charger. We just assume it's the same type of charger, so we can go with the same cost and price. Because down the line, the technology is going to evolve, then it wouldn't make sense for us to go with the slow charger.

00:14:21 Speaker 3
But the price is definitely different, a lot for now for fast and slow. So I think we should still do research on that difference.

00:14:29 Speaker 3
I think I'll do that. Put research.

00:14:34 Speaker 4
When I was talking to GPT, it did mention that perhaps like the fast chargers, it can be an enhancement for the model.

00:14:44 Speaker 4
Your base model can treat all charges as the same, so that you don't have too many variations of factors like fast versus slow. You just treat everything the same. Then, under your sensitivity analysis, you can have another enhancement. If you want to implement the fast charges, you put the constraints there. That's another alternative.

00:15:08 Speaker 2
That's might be easy way to do easier way to do it.

00:15:11 Speaker 4
Then you don't have to solve it.

00:15:12 Speaker 2
We don't have to think about so many factors.

00:15:15 Speaker 4
Put fast charges

00:15:16 Speaker 2
So you just put slow charges and then fast charger is like

00:15:20 Speaker 2
When you have money or want to think about it.

00:15:23 Speaker 3
That sounds like a good plan actually.

00:15:27 Speaker 3
Let's do that. Let me think.

00:15:30 Speaker 5
One question alone on the angle part.

00:15:32 Speaker 5
You mentioned only H. HDB car parks. We are not focusing on the private ones. Only the HDBs are focused on.

00:15:40 Speaker 1
Because the private ones, we don't have data in there.

00:15:44 Speaker 4
And the policy intent is different. Focus on HDB.

00:15:48 Speaker 4
I was just wondering whether we are looking at all HDB or zooming into a certain planning area.

00:15:57 Speaker 1
All HDBs around Singapore. We have the data for all of them.

00:16:03 Speaker 4
I guess the AI will be able to do that thing.

00:16:08 Speaker 4
As far as I'm not the one doing it.

00:16:11 Speaker 4
Okay,

00:16:17 Speaker 4
Erica, do you have any other questions?

00:16:20 Speaker 3
I'm just reading through my notes, but I didn't fact check this. Does Altan want to also optimize the CO two savings, fuel saving, MPV saving? A payback and more. Are we doing that? Can we do that? MPV savings.

00:16:37 Speaker 1
MPV savings.

00:16:39 Speaker 4
How do we?

00:16:42 Speaker 3
I think there was some mention of that, but I didn't really look into the files.

00:16:48 Speaker 2
I think it was under the plan dot MD one.

00:16:52 Speaker 3
I got.

00:16:55 Speaker 3
Again, it's not number.

00:16:58 Speaker 1
We don't have to go to CO two. I don't want to go there.

00:17:03 Speaker 3
Because I was thinking like this too much for fourteen days.

00:17:08 Speaker 2
We not. I think because in your split the parts right. You mentioned what one person will do M one to M five.

00:17:17 Speaker 3
Carbon cars

00:17:21 Speaker 2
Carbon tax, which is about the CO two emission factor, carbon tax, petrol car pump.

00:17:28 Speaker 1
Nah

00:17:30 Speaker 1
Let's not go there. I don't think I collected that data anyway.

00:17:33 Speaker 2
In the thing it writes to collect. We're going to do that.

00:17:42 Speaker 1
Oh no, there's a cross here. I think it means no.

00:17:46 Speaker 2
Oh no. But

00:17:48 Speaker 2
N collect seven is not public. But one to five is to collect.

00:17:55 Speaker 3
So I haven't collected data, but have to collect. The trick is you collected the data, which is called mysteriously.

00:18:02 Speaker 1
Let's not go there.

00:18:05 Speaker 2
We have less than fourteen days to do this, guys.

00:18:09 Speaker 3
Later for BB. I was like, cannot do this.

00:18:15 Speaker 2
How are we splitting the work?

00:18:22 Speaker 1
Um.

00:18:24 Speaker 1
I think right as not nowadays, like AI agent can do a lot, right?

00:18:32 Speaker 1
Why don't we just throw it there and see what is bizarre first, and then we be the reviewer. We give it comments and whatnot.

00:18:41 Speaker 2
But do we still need to find more data first, or do we have everything already?

00:18:47 Speaker 1
I think most importantly, data I use. Also use an agent to help me claw and help me find. So we can iteratively come back and check what it has clawed, what assumptions we have to make, what compromises we have to do.

00:19:04 Speaker 1
Because where my angle is that I don't mind spending work

00:19:08 Speaker 2
But AI can do it.

00:19:10 Speaker 1
Then do more. There's a communication. The biggest part will be a.

00:19:16 Speaker 1
The communication gaps between each person working on different parts of it. It feels more annoying that way.

00:19:24 Speaker 3
I feel like I think maybe we should let AI do it, but maybe we should assign a part to review. Each person should review one part so that at least we can fact check AI's work. Agree.

00:19:37 Speaker 3
Is that a better way to split the reviewing part?

00:19:43 Speaker 2
But maybe like, think out first.

00:19:46 Speaker 2
Maybe like 

00:19:48 Speaker 2
We should do two person reviews on one part just in case someone misses something.

00:19:52 Speaker 3
I don't trust myself. I also don't trust myself for this model.

00:20:00 Speaker 1
We have two angles. How about each

00:20:04 Speaker 1
Three people taking one, then one person can do the implementation and whatnot.

00:20:14 Speaker 2
One person do what?

00:20:15 Speaker 4
Implementation.

00:20:16 Speaker 1
Implementation.

00:20:17 Speaker 4
Run it with the AI agent.

00:20:19 Speaker 1
And then finally we have another person doing the report consolidation.

00:20:23 Speaker 1
Like that.

00:20:25 Speaker 2
Oh, okay, okay.

00:20:26 Speaker 3
I got it. I got it.

00:20:28 Speaker 4
I thought it comes together with the two angles because it's going to be in the same optimization model.

00:20:35 Speaker 1
That is true.

00:20:36 Speaker 4
You cannot run just one part.

00:20:40 Speaker 3
That is true.

00:20:45 Speaker 1
It's so funny because nowadays AI is a bit too good that we don't have jobs for everybody.

00:20:58 Speaker 2
This is how people are getting fired.

00:21:00 Speaker 3
You don't have much work to do, but you have to do some work.

00:21:06 Speaker 1
Ah, okay,

00:21:09 Speaker 1
How about this?

00:21:17 Speaker 1
You know what? That never mind.

00:21:19 Speaker 1
What do you guys think?

00:21:21 Speaker 3
My AI suggested we have one person be the model lead who asks the other two staff. Then we need a geography and supply person to do the data section in the report to make sure everything is fact checked and referenced.

00:21:40 Speaker 3
Then another person do demand to make sure the demand

00:21:45 Speaker 3
Fact check and reference in the report, of course, in the model also, and then our person do cost sensitivity analysis

00:21:55 Speaker 3
And I don't know the teacher method. What does it mean?

00:22:01 Speaker 3
Methodology. Fac facility location.

00:22:04 Speaker 3
I think. The data. Maybe. Facility data. Maybe facility data. Fact check everything.

00:22:11 Speaker 3
And last person do a review.

00:22:14 Speaker 1
Wait, I thought everyone was doing a review.

00:22:17 Speaker 3
But the last person can pair with someone to review. I mean, so that the last person has work to do.

00:22:29 Speaker 4
I think we can those few persons can check that specific part. Then the last person can make sure that everything is coherent. Cause we are all checking different parts.

00:22:38 Speaker 1
Fair enough.

00:22:39 Speaker 4
It's creating a job.

00:22:42 Speaker 3
That's what I've got to say.

00:22:44 Speaker 1
I'm filming right now, bro.

00:22:45 Speaker 4
I think something that we were just going to Erica.

00:22:49 Speaker 3
Thank you. After all, we need to prepare the report.

00:22:58 Speaker 4
After all, then we can do the report in that manner also. Erica, can you go to the Google Docs?

00:23:07 Speaker 3
I'm going to put in a

00:23:09 Speaker 3
Regan o Erica.

00:23:12 Speaker 4
Can you go to the prelim structure?

00:23:16 Speaker 4
Wow. So I was talking to GPT last night.

00:23:20 Speaker 4
Then I was thinking whether we have data for the cost part.

00:23:24 Speaker 4
You know the part.

00:23:26 Speaker 3
We don't. I think there is.

00:23:30 Speaker 3
This one.

00:23:30 Speaker 4
So that one will need some assumptions.

00:23:34 Speaker 4
I was looking at GBS and a few data sets to see whether we can.

00:23:39 Speaker 4
So I'll get a cost proxy, but I couldn't enter.

00:23:44 Speaker 4
Vigan, would you be able to? I don't know whether you work with the government. So you probably have a GP's account.

00:23:49 Speaker 1
I'm able to log in to see.

00:23:52 Speaker 3
Do that one, right?

00:23:53 Speaker 1
What the fuck?

00:23:56 Speaker 1
It's true. I do work with LTA, but I don't think I can smuggle anything out.

00:24:01 Speaker 4
Because this the tender sets are like for the tenderers, my the vendors to see for them to bid. So I thought you might have the access to go and look at the bids.

00:24:15 Speaker 1
Worst case scenario, we can research what brands are looking for and how much they're selling commercially. Then we do a slight markup from there. That also works. So these data, even though it's not in here, I'll try to fetch it. So thanks for pointing out.

00:24:36 Speaker 1
I'll close this gap.

00:24:39 Speaker 1
I'll ask the agent to review if we have any gaps to conduct this analysis based on this angle.

00:24:44 Speaker 1
Because when I did the data scraping, I wasn't fixed on a certain angle. So today we align, then I can go ahead and go back and take a look if we have any gaps or not.

00:24:58 Speaker 3
Cool. Now just remember, there's another cause in the gap.

00:25:04 Speaker 3
The penalty. I think there's a penalty in the model. In the defined model, there's a penalty cost for unmet demand. But we don't have the penalty cost.

00:25:14 Speaker 3
It's hard to find a penalty cost anyway. Maybe we just don't have a penalty cost.

00:25:22 Speaker 4
If you could scroll down, Regan

00:25:25 Speaker 4
Who's sharing? Is it Regan who's sharing?

00:25:27 Speaker 3
I think Regan.

00:25:29 Speaker 4
If we go down, I think GPT told me that if you can don't use the penalty way by doing a two stage optimization model. Where?

00:25:39 Speaker 4
You go down some more.

00:25:42 Speaker 4
Which one? So the alternative two stage optimization, then you don't need the p

00:25:48 Speaker 3
The penalty cost, because we don't have penalty cost.

00:25:51 Speaker 4
So that's why it suggested. Then we can AI decide.

00:26:00 Speaker 2
I see. That's a yeah, but also no, I also my GPT also said that if the penalty is too large, you just skew the model more towards places with demand, so it feels like maybe we shouldn't have it lah more than anything.

00:26:21 Speaker 4
I think it's difficult. If you choose wrongly, your model will not work now. So it has to be a very educated guess.

00:26:31 Speaker 4
So we see whether we can do the two stage one.

00:26:37 Speaker 4
I guess that'll be closer to what we learn in class also.

00:26:41 Speaker 1
Sure.

00:26:42 Speaker 1
But this is taught in class.

00:26:46 Speaker 3
The two stage one

00:26:48 Speaker 4
Yes.

00:26:50 Speaker 3
The stalker trick. The stalker stick. The stalker. Very good.

00:26:58 Speaker 2
Did you not study for your exam?

00:27:01 Speaker 1
We have to do good, guys. We have to do good.

00:27:08 Speaker 3
When should we meet next time and when should we start fact checking AI?

00:27:16 Speaker 2
Our next meeting is arranged on fourteen.

00:27:19 Speaker 3
Fourteen.

00:27:22 Speaker 2
Ten AM, right?

00:27:24 Speaker 1
Ten AM.

00:27:26 Speaker 3
Oh. Yes.

00:27:29 Speaker 1
Hmm. Oh, okay, okay.

00:27:32 Speaker 1
Yeah. All right.

00:27:33 Speaker 4
We always sound so surprised.

00:27:35 Speaker 2
As though we not, we did not send this out like last week.

00:27:40 Speaker 1
I just want to quiz you guys.

00:27:42 Speaker 4
Funny. Maybe we need it to depend on the person that is putting it into the AI and how fast it can be done.

00:27:53 Speaker 4
I presume the weekend will be the one.

00:27:57 Speaker 2
Yes.

00:27:58 Speaker 3
Let's do.

00:28:00 Speaker 2
So you tell us.

00:28:01 Speaker 4
2 p.m.

00:28:03 Speaker 4
I don't mind.

00:28:05 Speaker 3
M. Today. Oh my god, so fast.

00:28:07 Speaker 2
Looks like he's going hard today, so he has to finish before then.

00:28:10 Speaker 3
He has to be somewhere.

00:28:16 Speaker 3
Then should we pick our part so that

00:28:20 Speaker 3
Or we can pick it after the whole thing?

00:28:24 Speaker 2
I think you can just ask AI to assign us.

00:28:29 Speaker 3
Can AI never be good? Please, AI to talk to.

00:28:33 Speaker 2
Just once. Once you're done, just put it. Please assign who to review which part.

00:28:40 Speaker 1
Bro, it's like AI assigning us work right now. We're not assigning AI work.

00:28:46 Speaker 2
That's the design, right?

00:28:49 Speaker 1
Hey, come um.

00:28:53 Speaker 1
Who is doing what? Reagan is doing the building.

00:28:59 Speaker 1
The building part.

00:29:01 Speaker 3
AI building modeling part.

00:29:03 Speaker 1
What each what prop what portions we got?

00:29:09 Speaker 4
Erica, send it in one second.

00:29:11 Speaker 3
We already have five though. One is to fact check the demand and supply. There are two: one demand, one supply.

00:29:21 Speaker 3
And then the other one is to fact check the cost and sensitivity model analysis.

00:29:27 Speaker 3
The other one probably

00:29:30 Speaker 3
Uh,

00:29:32 Speaker 3
Wait, where did I?

00:29:34 Speaker 3
Okay,

00:29:35 Speaker 3
Methodology charging sites

00:29:40 Speaker 3
Location per square kind of stuff. They teach you a method.

00:29:47 Speaker 3
And then the last one is fact check, read through everything.

00:29:52 Speaker 1
Come the first, come first serve.

00:29:56 Speaker 4
Anybody got any preference?

00:30:01 Speaker 2
Wait, what?

00:30:06 Speaker 2
But this picture looks at looks seems different from what Erica said just out loud just now, though.

00:30:11 Speaker 3
It's right.

00:30:12 Speaker 3
I think that's what it meant, but it could be something else.

00:30:17 Speaker 4
I think it can be combined. Then we can have more people looking at one part together.

00:30:24 Speaker 4
Like the data section, I think it can be combined because we have all the data ready. We just need to review.

00:30:30 Speaker 2
So one person checks the model, one person checks the data, one person checks the sensitivity.

00:30:37 Speaker 4
Something like that.

00:30:39 Speaker 2
Then we can. Or two people each, but then Regan can exclude himself, so one part has to.

00:30:47 Speaker 2
I feel like the one.

00:30:49 Speaker 3
So you guys are saying one part to train the data, one part to train the model was the last part

00:30:54 Speaker 2
Sensitivity section.

00:30:57 Speaker 3
I feel like model and model power.

00:31:03 Speaker 3
We can multiple persons.

00:31:06 Speaker 1
It doesn't have to be one. So check data. I'll put my name there. But Sarah, you also want to do this? Sure.

00:31:15 Speaker 3
I feel like we get to take ourselves out though. You don't have to.

00:31:21 Speaker 2
It's fine. We just ask AI to do it.

00:31:24 Speaker 1
Sandra.

00:31:27 Speaker 2
It's just like an additional eye. I think two people do it is always slightly better.

00:31:31 Speaker 1
Sandra, do you want to?

00:31:33 Speaker 2
We can just assign, just do it.

00:31:36 Speaker 4
It's not related to anything.

00:31:39 Speaker 1
Can.

00:31:40 Speaker 3
You trust me so much.

00:31:43 Speaker 2
Okay.

00:31:45 Speaker 2
Sandra, this is what I choose.

00:31:47 Speaker 3
I choose. I choose.

00:31:49 Speaker 2
I choose. Give me her. Now my eye is reliable. You leave it to her.

00:31:56 Speaker 1
Then once everything is okay, likely where you guys are gonna check it from is from the GitHub repository. That's where I'll do all the work, model and whatnot. So actually, what you guys can do is just pump in that GitHub link into your AI agent and ask it to analyze and ask it to do the analysis from there.

00:32:19 Speaker 1
That might be easier.

00:32:21 Speaker 2
So. Then I'll then do we. Like the parts that we are doing, should we do the report of the parts that we are doing also?

00:32:28 Speaker 1
Can it?

00:32:31 Speaker 1
Can.

00:32:34 Speaker 2
And then should we have a deadline on when?

00:32:38 Speaker 2
Should we have a deadline on when we have to finish the report by?

00:32:43 Speaker 3
I think the skeleton can be on fourteen because there will be another week for us to modify something until this day.

00:32:52 Speaker 2
We can.

00:32:53 Speaker 2
So skeleton of the report to be up by fourteen also. Will you guys be able to do it? It's a bit of a rush.

00:33:00 Speaker 3
I have no idea. I don't know how much work. I buy AI.

00:33:07 Speaker 5
Maybe Sunday evening the next day, fifteenth.

00:33:11 Speaker 5
The skeleton of the report.

00:33:13 Speaker 3
Then we should.

00:33:14 Speaker 5
Saturday could be difficult.

00:33:16 Speaker 3
Then we should for our meeting on Sunday.

00:33:19 Speaker 5
For that, we can meet on Sunday.

00:33:21 Speaker 2
Give me a second. I remember that the reason why I put fourteen, there must be it. Let me check the previous timing that was confirmed. The poll.

00:33:34 Speaker 2
That was too long ago.

00:33:38 Speaker 3
Cause if not like, then there's no point to meet on Sunday because there is.

00:33:42 Speaker 2
Give me a second.

00:33:44 Speaker 3
No.

00:33:46 Speaker 4
I think it's a good point because three of us will be busy with our other report.

00:33:50 Speaker 3
Oh. Oh. That's true.

00:33:53 Speaker 3
I try to let AI do though. I don't feel. I don't plan on doing much work anymore.

00:33:58 Speaker 3
I'm in the holiday.

00:33:59 Speaker 4
You've already done your part.

00:34:00 Speaker 4
You've done a lot already.

00:34:04 Speaker 3
I don't want to feel.

00:34:06 Speaker 2
The available slot in our group chat is November fifteenth at eleven AM.

00:34:13 Speaker 2
Can lah. I think that was the only sort everybody could make it. But Regan here never confirmed. Fifteen November eleven a. Can make it. Because you did not vote.

00:34:25 Speaker 1
I say yeah can.

00:34:27 Speaker 2
Then let me change the meeting first.

00:34:31 Speaker 2
Eleven a.

00:34:32 Speaker 3
Then we can have our schedule turned out by then.

00:34:37 Speaker 3
Then the top of.

00:34:39 Speaker 3
What to change for the next week? Can we hear from me?

00:34:47 Speaker 2
Let's just finish it quick.

00:34:49 Speaker 4
Quick, and finish it.

00:34:51 Speaker 3
Let's also do a good job.

00:35:00 Speaker 4
Cause I really need the marks.

00:35:01 Speaker 3
I need it really bad.

00:35:07 Speaker 2
But we don't know your quiz yet.

00:35:08 Speaker 4
I know for sure. I'm gonna do.

00:35:11 Speaker 2
When I turned over

00:35:13 Speaker 5
I felt data. The data warehouses better.

00:35:19 Speaker 4
Correct. I'm gonna hear you.

00:35:24 Speaker 4
I guess we are kind of done.

00:35:27 Speaker 2
I send the new meeting

00:35:31 Speaker 2
Link. Really, you try now.

00:35:33 Speaker 3
Got it.

00:35:34 Speaker 2
Got it. So the next meeting is let's spin this down.

00:35:39 Speaker 5
So are we having the fourteen and fifteen too? I mean both also or only fifteen?

00:35:43 Speaker 2
There's just no fifteen. There's no need to have excessive meetings.

00:35:51 Speaker 2
Fifteen November, eleven a.m. Skeleton.

00:36:15 Speaker 1
Sounds good.

00:36:17 Speaker 1
Um.

00:36:18 Speaker 1
Anything else?

00:36:21 Speaker 1
If not, then I'll get to work.

00:36:24 Speaker 3
Thank you.

00:36:25 Speaker 4
Thank you for being nice.

00:36:27 Speaker 5
Thank you.

00:36:27 Speaker 3
See you on Wednesday.

00:36:30 Speaker 3
See you.

00:36:31 Speaker 3
Bye.
