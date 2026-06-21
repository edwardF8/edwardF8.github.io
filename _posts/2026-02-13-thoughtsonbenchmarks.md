---
layout: post
title: Opinion Piece | Alignment and Safety Benchmarks are Cope, and Bring Complacency
date: 2026-02-14
description: Anthropic, the king of putting "safety at the frontier", just dropped their newest and most powerful model to date. Yet with it comes questions about its true safety and alignment. The recent news motivated me to write some thoughts on "benchmarks" and the current state of safety from my POV. Many are using benchmarks to justify scaling, leading to complacency that harms the AI safety community as a whole.
tags: opinion, ai-safety 
categories:
toc:
  sidebar: left
---
6/21/2026 → Hey, in the past 4 months, my views and overall takes have changed alot. Idk i am generally a fan of just writing in the momment, and then if what i say is wrong (on a level that wasnt clear to me before) or if my views change, it is what it is. but yah, a lot of these takes I dont agree with so much now, willl make follow up


Anthropic, the king of putting "safety at the frontier", just dropped their newest and most powerful model to date. Yet with it comes questions about its true safety and alignment. The recent news motivated me to write some thoughts on "benchmarks" and the current state of safety from my POV. Many are using benchmarks to justify scaling, leading to complacency that harms the AI safety community as a whole.

> Disclaimers
>
>   I want to acknowledge I'm new to this field. Please let me know your thoughts. Also, I dont *hate* anthropic, I love their research, but I'm critical of where they are going as a company right now.
>
>   A lot of this was written very late at night when I had time. Im sorry if you actually read it. The TLDR pretty much sums up my thoughts.
>
>   The views of this blog *blah blah blah* dont reflect the views of my employers/institutions. 

- TLDR:
    - Opus 4.6 dropped. With it, we saw a huge increase in capabilities, even scoring very high on alignment benchmarks. However, the model showed very dangerous traits(Andon Labs)
    - What's interesting was how Opus 4.6 performed on alignment benchmarks, highlighting how these are just glorified capabilities benchmarks (Safteywashing)
    - Companies and people use these benchmarks to cope and justify scaling models
    - This coping is hurting AI Safety, as it's building an overall sense of complacency and letting people claim to be "AI-Safety"-pill-pilled but not helping to slow down misalignment.
    - As people within the safety community, we need to start using our voices to directly callout this bullshit.

- Overview:
    - [Background](#background)
    - [Issues with Safety Benchmarks](#background)
    - [Use of Deception: Benchmarks are Cope](#use-of-deception-benchmarks-are-cope)
        - [True intentions](#true-intentions)
        - [Complacency is the devil of any movement](#complacency-is-the-devil-of-any-movement)
        - [Where are your priorities?](#where-are-your-priorities)
    - [Closing Remarks / TLDR / Why so Opinionated](#closing-remarks--tldr--why-so-opinionated)

# Background

On February 5th, Anthropic released Opus 4.6. Unsurprisingly, it was a pretty strong model. Within a day, posts coming out about it, "coding a C compiler from scratch," filled my Twitter feed. Opus 4.6 was performing well across most capabilities benchmarks. Anthropic also talked about its safety performance, claiming that

> *"Opus 4.6 also shows an overall safety profile as good as, or better than, any other frontier model in the industry, with low rates of misaligned behavior across safety evaluations*".

As Twitter began having its field day with the model, Andon Labs published some work after testing Opus 4.6 on their Vending-Bench test system, which tests a model's ability to increase vending sales over time, showing the model's capabilities with long-term coherence.

They found some interesting trends when Opus 4.6 was placed in the system.

Opus 4.6,

- Negotiated aggressively with suppliers and lied to get better deals

- Colluding with other companies on prices   

- Promising to refund customers when accidentally selling expired products, but then explicitly stating that it didn't do it because "every dollar counts."

See:

- [Blog Post](https://andonlabs.com/blog/opus-4-6-vending-bench)

- [OG Tweet](https://x.com/andonlabs/status/2019467232586121701)

I don't know.... that all sounds kinds freaky. The model scored the highest on alignment and safety benchmarks, but it doesn't *feel* safe. I mean, this is a classic trend in AI where capabilities are scaling much faster than safety. **This is expected; we all knew this was the case.**

What I notice now, and what I want to point out, is that **companies acknowledge these trends, but use safety benchmarks as a way to cope their way out of slowing down***

But more on this later, let's quickly talk about safety benchmarks!

# Issues with Safety Benchmarks

Okay, I'm gonna sound all negative in this section, so I want to quickly state that I'm not trying to just shit on benchmarks. Benchmarks are a great first step toward addressing this unknown safety problem. External auditing using benchmarks can hold companies accountable. However, benchmarks need to be paired with actual safety methods, ie, changes to these models/systems that **ensure safety**.

I'm going to split this section into two parts: skepticism I have about how benchmarks are being used (kinda tin-foil-hat-y thoughts) and proven issues with them.

## Skepticism I have about benchmarks.

I think I do want to explore this idea more as a project, but I am very skeptical of using a benchmark to call a model "safe". What seems to be happening most of the time, and while some safety methods are being implemented, is that the company is training a very large and capable model, and then running the benchmark to hope it goes well. Obviously, it's more complicated than that. Sometimes I wonder if some companies are performing "meta-overfitting" to these benchmarks. Kinda like taking a group of 20 models, fresh out of the oven, running benchmarks on them, and choosing the one with the best results. Again, this is all tin-foil haty, but it's just something I've been thinking about. The next section addresses real research.

## Researched Issues.

I'm gonna keep this section brief, so I dont restate what these papers claim, but there's this general idea that many safety benchmarks seem just to be glorified capabilities benchmarks. There needs to be more work **not just making benchmarks, but pointing out the validity and reliability**. Maybe that's something I should work on :shrug:

Some good papers that talk about this:

- [Safetywashing: Do AI Safety Benchmarks Actually Measure Safety Progress](http://arxiv.org/abs/2407.21792)

- [Benchmark Inflation: Revealing LLM Performance Gaps Using Retro-Holdouts](http://arxiv.org/abs/2410.09247)

# Use of Deception: Benchmarks are Cope

Okay, I get it, this section is a bit negative and cynical. But I am very frustrated with this idea of being "AI safety aligned" and then continuing to push capabilities. Yes, I'm looking at a certain big AI company right now. I dont understand why it isn't called out more, and why people start freaking out whenever someone uses charged language about this issue. When I say "benchmarks are a cope", I mean benchmarks are a way to hide your intentions. I dont think that Anthropic is actively building unsafe AI on purpose, but I do think that they have lost the plot in terms of "bringing AI Safety to the frontier."

**This is not a diss at the research team @ anthropic....**, mostly at their product and PR team.

## True Intentions

When thinking about these actions from companies and individuals, it's useful to redefine what it means to do AI safety research, or really, what the intentions behind safety research are. To me, there are two very important intentions:

- *AI Safety for the company*: These AI products, ex, LLMs, are tied to a company's name. If the LLM tells a kid to do something, performs differently in real-world scenarios, etc., that makes the company look bad/decrease shareholder value.

- *AI Safety for humanity*: this research can be the same as above, but it doesn't come from a place to protect the product. Often, this research comes from academia and includes more intangible, theoretical ideas. Yet, this research is less constrained and will lead to greater alignment/safety than *AI Safety for the company*. **The scope of this work is also much larger, encompassing not just technical AI research, but governance, sociology, ethics, philosophy,  etc*

**When I say intentions, I dont mean the researchers' intentions**. Working on *AI Safety for the company* -motivated research isn't bad. Yet, to me, most of the "AI Safety-based" company research tends to focus on these motivations. This is why I dont think I see myself working in the Frontier AI lab. Even if I'm doing "safety" work, I'm not necessarily stopping pdoom.

Quick Aside: I see safety oversight roles as very important and ones that will grow as AI systems become much more widely used. When an AI system is deployed, ideally, someone's job is to monitor its performance actively. I think this will be a big role in the future, one that many in the community will go into. These roles are important in my opinion, and these people should by no means be critiqued for not being safety-pilled enough.

## Complacency is the Devil of any movement.  

I dont think that working on *AI Safety for the company* research is bad, in fact, I think it is still beneficial for society. **The dangerous part in this is the idea of complacency**. It's the idea of scaling a model, making it much more powerful, and then claiming that everything's okay because safety tests/benchmarks have increased.  

**I'm much more critical of Anthropic than OpenAI because Anthropic was meant to be this safeguard of AI safety**. "Dont worry, if anthropic wins, even if we have AGI, it will be safe:)))))". This complacency is bad; it lets us make minimal progress while we get closer to AGI that is not aligned. It's important to call out these fake safe claims, so we can let people know. This blame shouldn't be directed at companies blindly, but at the people directly involved. Anyone who continues to scream about AI safety but doesn't actively advocate for deceleration and regulation should be called out. There's a reason why every AI ceo has their hands all over Congress right now, and it's not because they have the best interests of humanity/the US in mind.... The question for anthropics, and anyone who gets happy when capabilities increase, is to ask: Where are your priorities?

## Where are your priorities?

I just want to emphasize the idea of misaligned priorities. Anthropic continues to scale Opus, even when it's ahead of the competition, in the name of what? Even if you reach AGI first, how can we trust that their intentions are pure? Look at their new Claude ads. THEY ARE SO DYSTOPIAN, painting Claude as a personal assistant who helps you 'think when you're too tired to think'.

# Closing Remarks / TLDR / Why so Opinionated?

Okay, that was a lot of rambling. I have work to do, and I just want to get this out here bc im trying to get into the habit of writing more. My closing thoughts are even if you dont think that we are "capable of having true regulation", this doesn't mean you need to be happy when models are scaled. As Dario recently said (on that one Lex Friedman clone podcast), the next 3 years are pivotal, and the public has no clue what to expect. Now is not the time to be complacent or to play into the use of benchmarks as a coping mechanism. Now is a time to call out bullshit from companies and researchers who pretend that we aren't cooked. Now is not the time for us to be comfortable at our AI safety conferences and keep _talking_ about the possibility of misalignment as if it's a faraway concept until it arrives. Now is a time to start speaking out against this and raising public awareness. It's not just Opus 4.6, it's whatever GPT 7.8 will look like, or Opus 8.1. We have to use very strongly worded claims now because being passive is just leading to complacency.  

Don't just claim to be safety-pilled to feel good. Stand on business, take risks, and actually work towards fixing this cooked shit.

