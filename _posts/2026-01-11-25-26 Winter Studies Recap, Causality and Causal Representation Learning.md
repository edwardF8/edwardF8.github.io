---
layout: post
title: 25-26 Winter Studies Recap, Causality and Causal Representation Learning
date: 2026-01-11
description: A primer on causality and causal representation learning(kinda)
tags: updates, guides
categories: 
---

(Will be updated soon -- Jan 11t, 2026)

I`ve spent most my break understanding the basics of causality and causal representation learning(CRL), and will most likely spend the next semester(and possibly next summer) working on some research problems that approach model interpretability with CRL. 

I thought it would be a good exercise to write up the overall idea of the concepts I learned over break, and hopefully anyone reading will find this interesting and be motivated to use CRL-basd methods in AI. I really do think that they are a very promising approach(granted we can get over some hurdles) to many problems in the safety community. 

> NOTE: I studied these topics through slides from 80-516(CMU Course) and focused more on the higher level topics. Hopefully this post wont embarrass me but if I get stuff wrong, sorry.  This is also very rushed, I have to start classes tomorrow but i`ve been meaning to get this out!



- TOC:
	- [Backstory/Inspiration](#backstoryinspiration) (You can Skip)
	- [Causality](#causality)
	- [Causal Models and Structures](#causal-models-and-structures)
	- [Traditional Causal Inference and Important Terms](#traditional-causal-inferencecausal-discovery-and-important-terms)
	- [Causal Representation Learning](#causal-representation-learning)
	- [CRL for Model Interpretablity](#applications-to-interpretability) 

# Backstory/Inspiration
You can skip this paragraph. I just wanted to give a bit of my motivation for why im interested in interpretability(i`m gonna call it interp for sake of typing). Ever since I got into AI in 10th grade, the idea of interpretability has been a large motivator in me continuing of studying the topics. 

I think interp has been changing like crazy and its not too well founded, so i`ll stick to the simple definition of "understanding why and how a model made a prediction"

For me, its a very satisfying problem to work on for three reasons:
- **Satisfying my Curiosity about AI**: Neural Networks(esp STOA AI) can do some pretty crazy things. But im lowkey less interested in what they can do, and more of *how* they do it. Interp can help us understand how models work and discover interesting trends, I think there is so much knowledge "behind the black-box" waiting to be uncovered. I`m very interested in [Ziming Liu`s idea of "physics of AI"](https://kindxiaoming.github.io/)
- **Satisfying my curiosity about the world**: I specifically remember during one of my first internships, I went to a local conference about AI in Material Sciences. One of the keynote talks was deriving physics equations using neural networks and interp. Ever since then, this "dream" of interp models to gain insight on the real world has been very promising.
- Satisfying my core value in having an ethical impact: Interp also helps out AI Saftey methods. I think theres much more to be said here, and honestly much more to be done. 

So, coming to CMU, I engaged in interp in two ways:
- A technical AI Safety reading group through my schools CASI that discussed interp. 
- Emailing interp PhD students/professors for opportunities and places to learn more.

This is when I meant [Xiangchen Song](https://xiangchensong.github.io/), who worked on CMU`s CLeaR lab. I read his position paper ["Position: Mechanistic Interpretability Should Prioritize Feature Consistency in SAEs"](https://arxiv.org/abs/2505.20254) which points out a key issue in traditional mech-interp methods that use SAEs. After calling with him, I became very interested in causality methods applied to interp. Thus, during this break, I began to study causality and CRL. Since I studied in a rushed way, I wanted to take this post to summarize what I learned (for me mostly....)


# Causality
> Association does not imply causation

This is the core principle behind causality. A causal relation is some relation where one event makes another event happen. Conditional Probability  $$ p(X\mid Y) $$  is the probability that  $$ X $$  occurs given  $$ Y $$  occurred. We can think of it like "**would  $$ X $$  happened if we find that  $$Y$$  happens?**". It doesn\ t track whether  $$ X $$  was the cause of  $$ Y $$  ( $$ X\rightarrow Y $$ ), whether  $$ Y $$  was the cause of  $$ X $$  ( $$ X \leftarrow Y $$ ), or whether they were both caused by some other variable( $$ X \leftarrow Z \rightarrow Y$$ ). Interventional Probability tracks this notion.  $$ P(Y \mid do(X)) $$  (where we call the action of  $$ do(X) $$  an *intervention*) asks, After forcing  $$ X $$  to occur, what is the probability of  $$ Y $$ . 

Causal Inference is the act of finding out *how much* one variable change`s another, or causal relations, but we will get to this later. 
# Causal Models and Structures
Before we get to finding causal relations in data, we should discuss how we actually represent causal mechanisms. We represent causal relations by using probabilistic graphical models. This section can be very theoretical, so i`m probably gonna skip a lot of the specifics and just give the overhead. 

### Side Note about Probabilistic Graphical Models
Given a set of variables $$ V $$, we represent causal relations as a directed acylic graphs(DAGs). Each vertex represents a distinct random variable, and the directed edges represent a causal relation. 

We call this DAG a **Causal Structure**. Problems either start with the causal structure predefined, or, one has to find this causal structure.  

We represent the entire scenario with **Causal Models**, where we specify both the causal structure and the associated conditional probability distributions for each random variable. Using causal models, we can ask questions about the underlying system under certain interventions(changes) and counterfactuals(what-ifs). 

Theres many different types of causal models, like causal Bayesian networks and structural causal models, which I dont have the knowledge to fully explain. 

But how do we get our causal model? We do causal inference on data. 
# Traditional Causal Inference(Causal Discovery) and Important Terms
Traditional Causal Inference isn`t too applicable to machine learning, but I think its important to discuss because the methods underpin any work with causality.

Traditional Causal Inference(which ill call Causal Discovery) focus on on finding causal structures from observed data in the case where the observed variables are the causal variables(in the CRL section, we will discuss why this usually isn`t the case for ML applications). 

##### Important Terms:
- Causal Variables: Factors/Attributes that directly influence changes in other variables:
- Confounders: Hidden variables that influence both the independent and dependent variables. 
- Causal Sufficiency: The assumption that all common causes of the variables have been studied, meaning theres no confounders in the dataset. TLDR: The data we have is enough to find a causal model thats legit. 
- Causal Identifiably: Sometimes, we can find multiple "equivalently" true causal models, so this just means we can identify a unique one. 
- Causal Minimality Principle: The simplest explanations are the better ones

Theres 3 types of methods for traditional causal discovery:
- Constraint-Based Causal Discover: 
	- These methods are based on the idea that conditional independence implies a candidate causal structure
	- The PC, FCI algorithms sort of focusing on cycling through candidate ones. 
	- Some of these methods only identify "markov equivalences" which are basically equivalently true (based on the data) causal models. 
- Score-Based Causal Discovery
	- These methods focus on searching over all possible causal graphs and finding ones that fit the data the best. 
- Functional Causal Model(FCM) Method.
	- This is sort of an outlier, but FCMs are a way to represent causal relations, so FCM methods try to find these causal models
	- Functional causal models(FCM) represents the effect as a function of direct causes and noise.  
	- Theres lots of types of FCMs, each brings its own "constraints" to the system which can help aid causal discovery (if you know more about the system)

# Causal Representation Learning
Traditional causal discovery relies on the assumption that the observed data are the causal variables. Yet for many modern data applications, this is simply not the case. Take image data. Your raw observed data are pixels. Yet, there aren\`t certain pixels that influence other pixels. The real causal variables(which we call latent variables) aren\`t in the observed data and need to be learned. 
This is where CRL comes into play, combing representation learning and causality. 

Specifically speaking, CRL aims to learn the latent variables that correspond to causal factors within the observed data. With CRL, one can potentially reveal hidden latent variables that "caused" the data to occur and get a causal model. With this causal model, one can set interventions and counterfactuals to edit the data distribution. 

Now, lets focus on more AI based problems. In most problems, the measured variables(like image pixels, or signal data) are just mathematical functions of latent causal variables. So often, we find functional causal models.

CRL becomes much more powerful when you can make assumptions, so exploiting temporal structure in data, distribution shifts ,multiple environments, etc. If the data is independently and identically distributed, with no parameters, its pretty hard and often impossible. 

A core idea is that you can fit a Gaussian distribution to nearly approximate almost any distribution. So CRL can be promising once you have the above constraints. 

Each constraint/situation brings a new method, for example if the data is from multiple distributions or if its temporal data. I think I still need to study these topics more, I might make another blog post about it later.
# Applications to Interpretability 
The last thing I covered during my break was the current applications to interp. I read two papers on this subject:
- [Beyond the Black Box: Identifiable Interpretation and Control in Generative Models via Causal Minimality](https://www.arxiv.org/abs/2512.10720) 
- [LLM Interpretability with Identifiable Temporal-Instantaneous Representation](https://arxiv.org/abs/2509.23323)

The first paper focuses on the idea that SAEs lack theoretical guarantees, and creates a framework that uses CRL to learn the true hidden variables that cause the latent space, creating more theoretically grounded results. I think one core note that stood out from this paper was the use of the causal minimality principle. Again this principle states that the best model is the simplest causal model consistent with observations. This allows them to enforce sparsity constraints which helps when doing CRL.

The second paper I read uses SAEs within the temporal causal discovery frameworks to discover interpretations within LLMs activations. 

This was quickly done in a couple hour before my first day of classes so its kinda rushed. I think I want to focus on a couple overall takeaways I have about this research:
- CRL provides theoretically grounded techniques, yet it cant scale to large dimensions, this is a large issue
- The causal minimality principle makes interp using CRL possible
- I need to study CRL more :skull: 


I kinda wanted to get it out there though, so hopefully if you read it you enjoyed.