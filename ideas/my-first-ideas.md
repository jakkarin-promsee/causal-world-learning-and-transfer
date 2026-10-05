> This is the story about Where did the ideas come from? What are my first insight and my target? (Only used for inspiration or the main direction; I don't have any references, and these ideas aren't refined yet. You can skip it if your purpose didn't want to understand the background insight or my reasoning)

# About myself

What have I done before?

1. I passed the competitive programming at the regional level. I built OOP in pure C (which doesn't have OOP) using pointer structures. 🗿🤣🤣💀 I was able to code game development with C#, able to code full-stack development with [HTML, CSS, JS, Node.js, React, TS, Next.js, etc.], able to write assembly or Verilog, etc. I like to understand mechanisms from the substrate upward. 🔥🤣🤣
    
2. I proved machine learning and deep learning without matrices to see how intelligence is kept in the numbers. I solved the derivative on paper and multiplied all the numbers by hand. 🗿🤣🤣💀 Then I wrote a deep learning library myself with NumPy to test my understanding. 🤣🤣
    
3. I deep-dived into gradient descent and the loss landscape in high dimensions to see how intelligence forms. Then I went on to solve the Hessian equation and build my own optimizer. 🤣🤣🤣 Next, I went to prove double descent with the soft and hard noise concepts. 🗿🤣💀
    
4. Then I went to challenge backprop, 'cause I think it isn't natural. I went back to the CPU/GPU substrates and designed my analog circuit with capacitors to make an efficient ALU with a forward-only learning concept. I ended up with defeat; it's right that backprop isn't natural, but it's the best way to assign direction. 🤣🤣💀 But I still got my model that is able to beat ER-strong in the continuous-learning field. (But it loses a bit on power usage.) 🗿🗿🤣🤣 But eventually I realized that this model is just a vehicle, not a soul of intelligence. I still lack the last pieces.
    
5. So I went to research latent space (h_t), inspired by CoT in LLMs. I picked the project Bounded-bandwidth visual reasoning that uses active-sensing glimpse selection to see, and lets h_t control it. (To see how the first latent is born, not using language because h_t is required from the start.) And yeah, I failed so badly at this. The h_t I got from it isn't the h_t I really want. I just got h_t that is just a static scratchpad, and a latent scratchpad alone is not reasoning. 🤣🤣🤣💀😭
    
6. This brings me to this current topic -> "beyond-backprop learning method"; below this line will be pure ideas that are not refined yet. The terms used below might not accurately reflect the full meaning I want. I may have overlooked or overclaimed something; there's no need to attack too aggressively. And some of these ideas may already have been explored. The purpose is just to make a milestone about my genuine direction. 🔥🔥🔥🔥

---

# Where did the original ideas come from?

Before I explain the beyond-backprop learning method, you have to understand first what the real thing I have been looking for is.

My last project, "Bounded-bandwidth visual reasoning using active sensing glimpse," asked the question: if a system has limited bandwidth, can the model select what to read and remember for recursive reasoning? (The model had to select (x, y, scale) to see some part of the real image, then had to predict the next (x, y, scale). The model had only 4 glances. I call this reasoning h_t.)

The negative result pushed me back so hard. To make h_t capable of recursive reasoning, we had to pretrain it a lot to make it understand what the reasoning really was. This was because because the gradient chain was not strong enough to train the entire model layer by layer. Normal training would make the top layer shallow; therefore, the bottom layer would not have enough information to send for reasoning.

(The selecting model had about 3 layers of abstraction. There were three layers: how to read a single glimpse, how to read T glimpses, and how to reason to predict those (x, y, scale).)

At first, I thought this previous topic would be heavy on h_t-type optimization. But synthesizing the relational dataset and making those pretraining courses took me about 90% of my time; about 2 months. I ended up finding that the h_t I obtained was effectively static. The model used the initial input to construct something closer to a complete action plan or TODO list, then executed that plan across later glimpses. New observations did not meaningfully restructure its internal belief or future reasoning. It could carry a plan across time, but it did not truly think across time. (But this h_t still beat the base model. h_t is really useful and has an advantage there. It's just not the thing I'm looking for. 🤣🤣)

TL;DR: What I found is:
1. h_t has many types, and the type I'm looking for is recurrent reasoning.
2. Training alone isn't enough; we also need good pretraining to build abstract layers layer by layer.
3. The old dataset and position aren't good for reasoning. It's so hard to synthesize a new dataset or make a pretraining dataset.

And it brought me to a sharper direction; the current topic is the beyond-backprop learning method.

---
# What is the "beyond-backprop learning method" ? (First concept)

There is one question that I somehow never seriously asked during almost 4 years of researching deep learning:
> Does human intelligence really need to train from a dataset that contains every possible way of solving a problem?

It's true that humans still use credit assignment. Dopamine, success, failure, reward, or punishment; some form of feedback clearly exists. 

But human learning does not look like normal deep learning at all. For example, how can I read Newton's law, see only a few examples, and then apply it to situations that I have never seen before?

While my DNA did not inherit Newton's law, my brain neural connections were not copied from my parents. And I did not need millions of shuffled examples of every possible object falling in every possible situation. I only needed the concept.

This becomes even stranger when compared with current training algorithms. Modern models rely heavily on the distribution of their training data. When we introduce new data, we often have to mix it with old data again to prevent **catastrophic forgetting**. Even learning rules inspired by Hebbian learning still face some version of this limitation.

Human learning seems very different; A human can read a book, watch only one or two real examples, and suddenly gain a model that can be reused almost anywhere they want. 🤯🤯.
> For more precise: Humans can use enormous amounts of prior structure to turn a tiny amount of new evidence or symbolic communication into a large change in their internal world model without retraining the entire substrate.

That gave me another idea:
1. What if human credit assignment is not mainly training input to output mappings like normal deep learning? 
2. What if it is mainly training the perception and internal model of the world that later reasoning operates on?


Maybe the system should be separated into different parts:

**1. The inherited neural model**
Human starts with some core mechanisms inherited through biology like DNA. This model does not directly contain knowledge like how to cook, how to use calculus, how to speak a particular language, or how to solve a physics problem. Instead, maybe it mainly provides the mechanism required to **form perception and construct a model of the world**.

I currently imagine it something like an simple RNN whose initial (h_t) contains almost nothing useful about the current world, but whose fixed structure knows how to read, update, and organize (h_t) into a reasoning model of the world. 🤯🤯


**2. The pretraining from other humans and the world**

Parents, teachers, books, society, language, or personal experience; all of these continuously shape the internal model. This is the part I am most interested in now. 

A human brain without this inherited knowledge from previous generations would still be able to survive and learn something. But it would not start from the accumulated causal structure that civilization has already discovered.

We do not inherit neural weights from previous humans. Instead, we inherit compressed models of the world through language, teaching, books, equations, tools, and culture.

---

# Refine the scope

So maybe the problem I actually want to study is not how to build a complete intelligent system. That problem is way too large anyway. 🤣

The question is much smaller:
> What is the minimal sufficient internal state for inferring and updating the causal structure of a bounded family of environments instead of exhaustively trying everything?

And then there is a second part:
> How should this representation be pretrained or transmitted so that one agent can pass useful causal structure to another agent without directly sharing its weights or raw experience?


In other words, I am interested in two things:
1. how a mostly fixed model with a flexible (h_t) can build a useful model of the world from very few samples;
2. and how that learned structure can be compressed and passed forward, like knowledge being handed down through books across generations.

Maybe "beyond-backprop" is not about finding another local update rule that replaces gradient descent. Rather, it may be a post-backprop learning rule for figuring out what should be learned slowly, what should be inferred quickly, and what structure must exist before credit assignment at the next level even becomes possible.

TLDR:
>Intelligence may depend less on rapidly modifying the neural substrate and more on having a slowly learned mechanism capable of constructing, revising, and transmitting compact causal models inside a fast-changing internal state.

---
