---
layout: about
title: about
permalink: /
subtitle: CS @ <a href='https://www.cs.cmu.edu/'> CMU</a> | Intern @ NIST under <a href = 'https://www.nist.gov/people/william-d-ratcliff'>Dr. Ratcliff</a> & @ CMU under <a href = 'https://xiangchensong.github.io/'>Xiangchen Song</a> 
profile:
  align: right
  image: mainphoto1.jpeg
  image_circular: false # crops the image to make it circular
  more_info: >
#    <p></p>
selected_papers: true # includes a list of papers marked as "selected={true}"
social: true # includes social icons at the bottom of the page

announcements:
  enabled: true # includes a list of news items
  scrollable: true # adds a vertical scroll bar if there are more than 3 news items
  limit: 3 # leave blank to include all the news in the `_news` folder

latest_posts:
  enabled: true
  scrollable: true # adds a vertical scroll bar if there are more than 3 new posts items
  limit: 3 # leave blank to include all the blog posts
---

<p class="small-note">
the way I cope with my insecurities is by studying  🙏 (I just enjoy learning)
</p>

<div class="substack-pills">
  <a class="substack-pill" href="{{ site.substack.personal.url }}" target="_blank" rel="noopener" title="{{ site.substack.personal.name }} on Substack"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M22.539 8.242H1.46V5.406h21.08v2.836zM1.46 10.812V24L12 18.11 22.54 24V10.812H1.46zM22.54 0H1.46v2.836h21.08V0z"></path></svg>personal substack</a>
  <a class="substack-pill" href="{{ site.substack.ai_safety.url }}" target="_blank" rel="noopener" title="{{ site.substack.ai_safety.name }} on Substack"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M22.539 8.242H1.46V5.406h21.08v2.836zM1.46 10.812V24L12 18.11 22.54 24V10.812H1.46zM22.54 0H1.46v2.836h21.08V0z"></path></svg>ai safety substack</a>
  <a class="substack-archive-link" href="{{ '/blog/' | relative_url }}">blog archive &rarr;</a>
</div>

---


<ul style="list-style-type: disc; padding-left: 2rem;">
  <li>Second Year @ CMU SCS | See my <a href="cmucourses">course reviews</a></li>
  <li>Executive Board Member for <a href="https://cmuaisafety.com/"> Carnegie AI Safety Initiative (CASI)</a>, Co-running intro technical AI Safety reading groups and working on initiatives to engage the public on AI threats and AI regulation.</li>
  <li> Also a TA for <a href="https://s22.cs251.com/index.html"> 15-251 <em>Great Ideas in Theoretical Computer Science</em> </a>,  CMU's main undergraduate introduction to theoretical computer science and "theoretical thinking"</li>
  <li> Placeholder for whatever seems seems the most important rn (which changes alot)  </li>
</ul>

<style>
  .home-now-wrap { margin: 0.6rem 0 0.2rem; }
  .home-now-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--global-text-color-light); margin-bottom: 0.4rem; }
  .home-now-more { font-size: 0.72rem; margin-top: 0.35rem; }
  #lf-now.lf-now { display: flex; align-items: center; gap: 0.8rem; max-width: 440px; min-height: 60px; padding: 0.6rem 0.8rem; border: 1px solid var(--global-divider-color); border-radius: 10px; background: var(--global-card-bg-color); box-shadow: 0 3px 10px rgba(0,0,0,0.05); }
  #lf-now .lf-hero-art { width: 48px; height: 48px; border-radius: 6px; object-fit: cover; flex: none; }
  #lf-now .lf-initial { display: flex; align-items: center; justify-content: center; background: hsl(var(--h, 280), 45%, 55%); color: #fff; font-weight: 700; }
  #lf-now .lf-badge { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--global-theme-color); display: flex; align-items: center; }
  #lf-now .lf-eq { display: inline-flex; gap: 2px; align-items: flex-end; height: 11px; margin-right: 5px; }
  #lf-now .lf-eq span { width: 3px; background: var(--global-theme-color); animation: lf-eq 0.9s ease-in-out infinite; }
  #lf-now .lf-eq span:nth-child(2) { animation-delay: 0.2s; }
  #lf-now .lf-eq span:nth-child(3) { animation-delay: 0.4s; }
  @keyframes lf-eq { 0%, 100% { height: 4px; } 50% { height: 11px; } }
  #lf-now .t { font-weight: 600; color: var(--global-text-color); font-size: 0.92rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  #lf-now .a { color: var(--global-text-color-light); font-size: 0.8rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>

<div class="home-now-wrap">
  <div class="home-now-label"> headphone lens: </div>
  <div class="lf-now" id="lf-now"></div>
  <div class="home-now-more">apologize for explicit images that are album covers <a href="{{ '/music/' | relative_url }}">→ more music stats here</a></div>
</div>

<script>
  window.LASTFM = { user: "{{ site.lastfm.username }}" };
</script>
<script src="{{ '/assets/js/lastfm.js' | relative_url }}"></script>

---

###### **Short Term Interests**: 
Whatever makes AI go best for humanity! 
- **Research**: Misalignment science in models and monitoring misalignment, technical AI governance research, assisting a slowdown in AI development  
- **AI Safety Field Building**: Getting more writers/design/comms folk into AI Safety, working on informing the public about the future of AI and generally increasing the diversity of the field. Also convincing systems, security, and ECE people at CMU to work on Compute verification research, and in general convincing CS/CS-adjacent students to work on AI Safety.

###### **Long Term Beliefs**:
The future seems very uncertain, so its hard to say what I want to work on / am interested in. Broadly, these are my values/beliefs/motivations
- I find myself happiest when I'm teaching others and learning about nuanced problems. 
- Every human has critical flaws, insecurities, and irrationalities, but these are what make humanity so beautiful. 
  - Lots of irrationalities stem from material conditions that stretch them too thin, though this might be hard to truly address 
- Achieving the most **equitable** future is one of my most important values, I focus on equity as most suffering and pain is _hidden_ behind the systemic barriers in our society
- The system we live and work in inherently works against these interests, yet I (as a straight white Jewish man) likely receive the least repercussions; acknowledging this means understanding that I might be more inclined for passive means of change / satisfaction with the status quo. Though I still believe in changing the system from within 
- I plan to **never work for big tech**, though I could see myself working on partner projects or as part of certain fellowship programs. If this situation occurs, I hope to write about in-depth and get feedback on my choices. **Please hold me accountable to this!**

###### Personal Bio:
For a long time, I dreamt about going into academia, doing independent and impactful research while having the intellectual freedom to speak on important issues (Noam Chomsky type). However, the uncertainty of the future has changed my view on  

Outside of "work", I like working out, running, music, learning ab random things, watching slop, and talking ("The Eddie Problem"(which i will write about soon ))