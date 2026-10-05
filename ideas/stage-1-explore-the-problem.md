> This draft is writing about main concept for core experiment. It's about how we define dataset and h_t. Explore how to make it can infer and update the causal structure of bounded family of environments

## The project's core direction

The direction separate to 2 part, there is:
1. What is the minimal sufficient internal state for inferring and updating the causal structure of a bounded family of environments instead of exhaustively trying everything?
2. How should this representation be pretrained or transmitted so that one agent can pass useful causal structure to another agent without directly sharing its weights or raw experience?

The working step designed with:
1. Building the minimal sufficient environment and model's internal state that can be working
2. Exploring the model behavior in each environment type
3. Expand the environment law to be complex and sequential.
4. Building the minimal sufficient communication channel between 2 agent that can transmit useful causal structure.
5. Exploring the transmit behavior in each environment and communication type.
6. Moving to the real world dataset...

---
## What should dataset look like?

Before design the model, first we have to define what is a **causal structure**, **what gradient is learning**, and **what h_t is learning at post backprop**.

## 1. Define the environment law 

The relation/law should be like a graph, but this graph should have plenty of node relation to prevent the model remembering all possible graph itself. 

With the graph properties we can define something like "do A, get B", "do A or C, get D", "do B get C", etc. That is the law of action and reaction.
   
The h_t will keep belief from past experiment that have done before. There is h_t that keep belief of the world model from ["result from doing y", "result from doing x", ...] -> select next experiment (such as "do z") -> get result -> h_t update its belief -> more experiment

The model will keep only how to infer and update belief from its experiment that is bounded environments. It should not remember all law in dataset. Rather, it should only remember how to find those law.

---   
## 2. Define the dataset

The requirement we want:
1. It should have a law that produce set of relation; model can interact with environment
2. It should have a plenty of law that we can openly select the distinct law for each data sample; it will prevents the model remember all law itself.
3. It should can separate to both one step thinking and many step thinking; it will use to test model from simple to complex task.

So the ideas I think now is "building my own micro universe. each data sample is 1 universe that have a unique law. And the model can't read a law directly, It has to read via experiment from element itself"

### What dataset look like for 1 sample?

this is 1 sample data or 1 micro universe:
1. The micro universe is closed, it has only $S = \{0, 1\}$. (simplify that relation)
2. The micro universe has selected 3 law, there is $F = \{AND, OR, NOT\}$. (From many Boolean operator like XOR, NAND, NOR, etc. ). And we won't tell the model which law we use in this micro verse.
3. The micro universe have 2 independence particle, there is $X = \{A, B\}$. And having 4 dependence particle, there is $Y = \{C, D, E, F\}$. Which model can change value in only X. Because sometimes Y isn't 1:1 function, such as AND or OR operator. (But NOT is)
	1. A = random initial number
	2. B = random initial number
	3. C = NOT(A)
	4. D = AND(A, B)
	5. E = OR(A, B)
	6. F = AND(C, B) // complex task that is AND(NOT(A) , B)

So in t=0 (The initialization), we will get:
- X = [0, 1], Y = [NOT(0), AND(0, 1), OR(0, 1), AND(NOT(0), 1)] = [1, 0, 1, 1]

At t=1, the model have to select which X they will use for experiment. Such as model select to do X_0 or A = 1 (B still be 1 from previous environment). We will get:
- Action: nothing -> X_prev = [0, 1], Y_prev = [1, 0, 1, 1]
- Action: do X_0 = 1 -> X_now = [1, 1], Y_now = [0, 1, 1, 0]

Then At future t, The model will keep old experiment result,  infer its belief on that data, and select next experiment to update its belief. 

And we won't let's the model to do every possible way in X which is [0,0], [0,1], [1,0], and [1,1] now. We will let's the model do only 2 experiment then let's it's predict the all micro universe law. Therefore we have to compute sample space amount for every micro universe generate to make sure that we didn't leak the law information directly to it.

Finally, the model will get only fix 6 input and 6 output / experiment, it see only X and Y without even a glance of world index, world law index, or world law type.

More over, with only $F = \{AND, OR, NOT\}$, we also able to make something like XOR by OR(AND(A, NOT(B)), AND(NOT(A), B)). Or making complex relation $X = AND(A, B)$, $Y = OR(C, D)$, $Z = AND(X, Y)$. Now Z can write in Boolean algebra with $Z = A \cdot B \cdot C + A \cdot B \cdot D$, which it has 2  complex term, making model have to understand how to solve complex relation.


### What dataset look like for all?

It will look like series datasets each sample have its own micro universe law that can produce series data from t=0 to n.

The normal series dataset is that x connect together via t. Such as x is product sales on time. x_1 is t=1, x_2 is t=2, etc. And they will cut the X by range, such as 1 sample have 6 time length. Such as:
-  X_1 = x_1 to x_6
-  X_2 = x_7 to x_12
-  X_3 = x_13 to x_18

While our series dataset is that all X distinct together by law. But inside X_n series, they still connect together. Such as:
- X_1 = [$S = \{0, 1 \}$, F={AND, OR}, X(independence particle)={A, B}, Y(dependence particle)={C, D, F} ]
- X_2 = [$S = \{0, 1 \}$, F={AND, OR, NOT, COPY}, X(independence particle)={A, B}, Y(dependence particle)={C, D, F, G} ]
- X_3 = [$S = \{0, 1 \}$, F={XOR, NOR, OR}, X(independence particle)={A, B, C, D, E}, Y(dependence particle)={F, G, H, I} ]

Each X_n can produce a plenty of x (The all possible x = size(X)^size(S) ). And the series inside X_n was determine by the model via selecting experiment. Which model can't see all possible x and have to guess each X_n world law from bounded experiment.

More over, the variable S, F, X and Y didn't fix to only in world binary. I just pick simple Boolean function to explain you now. The main field I interest now is transformation on 2D. Because Boolean have so less resolution that S is only {0, 1}, it may making training is so hard and model's experiment is so hard to interpret.

On the other hand, if we use 2D vector and transforms function, we can get more sample space from size(X)^size(S) law, cause the X now is R^2.
- S = vector 2D that is R^2 on Euclidian such as (1, 1) or (1, 2) 
- F = {shift (R^2), resize (R^2) , rotate (0-2pi), square, square root, unique function (x, y) to (2x + y, 1), unique function (x, y) to (x^2, x + 2y), etc.  }
- X(independence particle) = {A, B, C}
- Y(dependence particle)={D, E, F, G, H, I}

The model loss function will be more detail. The model's experiment will more easy to interpret. For instance at Boolean world, AND(1, 1) = OR(1, 0) = OR(0, 1) = OR(1, 1) = NOT(0), this occur because sample space on Boolean is so small, and this can make function represent collapse. While on 2D vector, only shift operator can make (x, y) to (x + a, y + b) which a, b in R. 

More over, we didn't need to use full R that have infinity point. We can scope it into $[-10, 10]  \in I$ that have only 21 point. This will making possible Bayesian analysis. (if F(X) get 1.6, we will round up to 2. Or we won't make it get into this situation at first.)

We can go more farther and farther, such as 3D/4D/5D vector, change Euclidean to spherical/elliptical/hyperbolic, make the F from linear function to non linear like activate function or even a MLP, add noise to dependence particle, etc. But now we will stay at simple Boolean first, cause it's easy to define a thing.

---

## 3. Define the model and h_t (Revision 1, Outdate now, Go to 4.)
> This draft is outdate now. But not because it's wrong. Rather it's because this draft is too complex and get boundary of h_t and z explode problem. And it's still worth to read, most thing in this draft has been rewritten to be more simply or correct at topic 4.

Assume that we use simplify Boolean micro universe where:
- $S = \{0, 1 \}$
- $F = \{AND, OR, NOT \}$
- $X = \{A, B, C, D\}$
- $Y = \{E, F, G, H, I, J\}$

The all possible experiment is 2^4 = 16, it may not small or large much to track how model think. The Y > X will make multivariable equations solvable. And X, Y > F will make all law function solvable. Therefor, I think this setup will have enough experiment step and at the experiment 16 will can make model can solve all Y variable, and can solve all universe law. 

### What is rough concept about the model and $h_t$?

Next I will explain the main variable for the model formular below. Because the set {S, F, X, Y} is a representation for only 1 micro universe, not a thing that model formular can use. There is:
1. $h_t$ = hidden state about the model's belief how universe law at t is (universe law on F)
2. $a_t$ = action that model will do at t (model's experiment on X (independence variable))
3. $o_t$ = observation from that action t (experiment result on Y (dependence variable))

And the definition of word we frequently use:
1. $experiment_t$ = the pair of $a_t$ and $o_t$ from belief $h_t$
2. $environment$ = the relation of Y (dependence variable) from X (independence variable) by set function F.


For the information flow:
$$
a_0, o_0, h_1 =\text{init world} \rightarrow a_1 = f(h_1, a_0, o_0) \rightarrow o_1 = f(a_1) \rightarrow h_2 = f(h_1, a_1, o_1) \rightarrow \text{next }a_2...
$$

At t=0, all value will be fix initial. Then at t>0 we can write formular to:

1. $a_t = policy(h_{t}, a_{t-1}, o_{t-1})$ : 
   $a_t$ will compute from $h_{t}$ (what is model belief about world law at t), $a_{t-1}$ (what is previous action), and $o_t$ (what is previous observation). This information may enough to compute next action. (I don't sure that give the model only last 1 previous experiment step is enough or not)

2. $o_t = intervention(environment, a_t)$ :
   The observation when do $a_t$ to current $environment$. (Getting the result)

3. $h_{t+1} = f(h_{t}, a_{t}, o_{t})$ :
   Then $h_{t+1}$ will update from $h_t$ (Old belief before doing experiment), $a_{t}$ (The action from that belief), and $o_{t}$ (The observation from that action). 

### What is the model and h_t really is?
> Below this section will be my 100% opinion ideas that I don't sure will it really work or not. It's working space that we can delete or rewrite it all anywhere. Therefor, if you have any ideas, optimize, see something wrong, or something. You can suggest me.

First, I will assume that now in every micro universe have equal X (independence variable), Y (dependence variable), and  F (law). That is we have map X, Y, and F shape across whole micro universe.

Caution a bit. The F that we call "law" is a basis law. While the function from X, Y to Y such as Y_0 = AND(X_1, X2) and Y1 = AND(Y0, X3) also call "law" too. The F set use to manifest the boundary of universe relation and make a convenient for us to handle X, Y to Y relation. And the "law" I talk about in the below will often be "the function from X, Y to Y". One AND law can produce countless function from X to Y. Such as X = AND(A, B), Y = AND(X, C), Z = AND(X, D), etc. Therefor, The "law" from model's sight isn't a F, but it's rather a "Function from X, Y to Y". Such as if F = {AND, NOT}. The model have no clue what we really define F, It can think like F = {NAND, NOT} or a {NAND(a, b), NAND(a, a)} or even {NOR(NOR(NOR(a, a), NOR(b, b)), NOR(NOR(a, a), NOR(b, b))), NOR(a, b)}. This all still is same function that can do {AND, NOT}.

(The reason that I write "from X, Y to Y" while eventually we can solve algebra until get "from X, F(X) to Y" is because it's more freely open for model to build a Y. It can pick y directly without reforming that whole Y from X again)

### 1. What h_t represent now?

First, we have $H_t$ that is all experiment experience in all time that didn't compress or reduce:
$$
Ht​=(a0​, o0​, a1​, o1​, …, at−1​, ot−1​)
$$

We want model's that decide action ($a_t$) via it all experience:
$$
at​=\pi(H_t​)
$$

But history growth larger and large, So we make $h_t$ that is fixed bandwidth to represent all history $H_t$:
$$
h_t = \phi(H_t)
$$

Then mode's decide its action via $h_t$ instead:
$$
a_t = \pi(H_t) \quad \rightarrow \quad a_t = \pi(h_t)
$$

While $h_t$ didn't lose important data:
$$
   z=f(h_t) = f(H_t) \quad \rightarrow \quad p(z\mid h_t) \approx p(z\mid H_t)
$$
- $h_t$ represent compressed belief of the whole world law. There is all experiment, the X/Y relation, next action, etc." and 
- then $z$ use information inside $h_t$ to create its belief world law ($z$). There is only what law this universe have from all observation information 0 to t.
- and then $p(z \mid h_t)$ use to represent the probability of each z law, when we do only experiment 0 to t" .

Finally, we get information flow:

$$
H_t \rightarrow h_t \rightarrow z \rightarrow p(z \mid h_t)
$$

### 2. The h_t slot ($h_t^n$) concept

Next problem is "How will $h_t$ alone keep all world law?". My ideas now is making $h_t$ for size(Y) slot, mapping to each $y_i$. The $h_t$ slot 0 or write to $h_t^0$ mean to "What is the model's belief about world law of $y_0$. (The 0's law) How does $y_0$ function is constructed from $X$?".  For instance:

| Y   | Actual Y = f(X, Y)       | h_t (What model's belief about Y now)            |
| --- | ------------------------ | ------------------------------------------------ |
| y_0 | y_0 = AND(x_0, x_1)      | h_t^0 (The model's hypothesis of Y_0 from F(X) ) |
| y_1 | y_1 = OR(x_0, x_1)       | h_t^1 (The model's hypothesis of Y_0 from F(X) ) |
| y_2 | y_2 = AND(NOT(y_1), x_1) | h_t^2 (The model's hypothesis of Y_0 from F(X) ) |

Write back to formula:

$$
y'_n = f(h_t^n, X, Y), \quad e_t^n = y'_n - y_n 
$$
- $y_n$ = actual y (independence particle) from micro universe initial
- $h^n_t$ = h_t at slot n about "how does y_n is constructed from all set X"
- $y'_n$ =  the function that model belief about what y really is at t (Or calling model's hypothesis)
- $e_t^n$ = the correctness of model's hypothesis after do experiment. (Chaining X, then watch the changes of $y'_n$ and $y_n$)

### 3. What z really is?

This may be the hardest part to define. The (z) represents the model's final belief about what the formula of (Y) really is. The problem is that even if we limit the model to a small set of basic laws, there can still be many possible formulas. We can roughly think of the number of possible formulas as growing with size(F)^composite_step.

For example, if $F = \{AND, OR, NOT \}$ and the maximum composite step is 3. The model can build formulas like AND(a, AND(b, AND(c))) or many other combinations of the same basic laws.

So instead of thinking about (z) as an unlimited set of every possible formula, we can limit the space by fixing the basic law set (F) and the maximum number of composition steps. 

My ideas now is defining z to "the represent of belief about Y formular that create from n step using the world basis law". That is z = [composite_step_1, composite_step_2, ..., composite_step_n].

Define the atom:
- The world basis law: F = [AND, OR, NOT]
- Operator slot (opts): probability of the basis law  = [p(F_0), p(F_1), p(F_2)]
- Operand slot (oprs): probability of selecting input = [p(x_0), p(x_1), p(x_2), p(y_0), p(y_1)]

Define the composition workflow:
1. At n=1:
	- operator slot (opts) = [p(F_0)=0.7, p(F_1)=0.1, p(F_2)=0.2].
	- argmax(opts) = F_0 = AND operator which is function : (S, S) -> (S)
	- operand slot (oprs) =  [p(x_0)=0.5, p(x_1)=0.4, p(x_2)=0.1, p(y_0)=0, p(y_1)=0]
	- argmax_2(oprs) = [x_0, x_1]. (AND operator require 2 input)
	- implementation: a_1 = AND(x_0, x_1)
	- completion (push a_n into oprs) new_oprs =  [p(x_0), p(x_1), p(x_2), p(y_0), p(y_1), p(a_1)]

2. At n=2:
	- operator slot (opts) = [p(F_0)=0.0, p(F_1)=0.6, p(F_2)=0.4].
	- argmax(opts) = F_0 = OR operator which is function : (S, S) -> (S)
	- operand slot (oprs) =  [p(x_0)=0.1, p(x_1)=0.1, p(x_2)=0.4, p(y_0)=0, p(y_1)=0, p(a_1)=0.4]
	- argmax_2(oprs) = [y_0, a_1]. (OR operator require 2 input)
	- implementation: a_2 = OR(x_2, a_1), that is a2 = OR(x_2, AND(x_0, x_1))
	- completion (push a_n into oprs) new_oprs =  [p(x_0), p(x_1), p(y_0), p(y_1), p(y_2), p(a_1), p(a_2)]

3. At n = 3:
	- looping opts -> argmax(opts) -> oprs -> argmax(oprs) -> implementation -> completion


This making the model didn't have to build it own world law like {AND, OR, NOT}. This model itself didn't need to keep a weight for do {AND, OR, NOT, NOR, XOR, etc.} across many micro universe. It just know there are 3 unknown law that can be used by just select opts slot index, then getting final  sequentially composite graph. The answer for Y function didn't fix to only 1 answer. The model can use any operator it want, by just complete it in n composite step. Such as NOT(NOT(A))=A, AND(A,B)=AND(B,A), OR(A,B)=OR(B,A), etc.

The only thing to watch out for is just calling Y operand repeatedly in the experiment. It's certainly that 3 composite step is the boundary. But if y_0 have 3 composite step. Then y_1 call y_0 again, it can make 6 composite step itself. 

Same with a_n variable that model will it into oprs array at completion step. if a_0 call y_0 that have 3 composite step. Then it a_1 call a_0, the boundary still be increase.


Therefor, now our z (belief about what the formula of (Y_n) really is) will look like:
$$
z_n =

\begin{bmatrix}  
	
	\begin{bmatrix} opts_n^1 \ oprs_n^1 \end{bmatrix} \\
	
	\begin{bmatrix} opts_n^2 \ oprs_n^2 \end{bmatrix} \\
	
	\vdots \\
	
	\begin{bmatrix} opts_n^m \ oprs_n^m \end{bmatrix} \\

\end{bmatrix}

, \quad

z =

\begin{bmatrix}  

	\begin{bmatrix} z_1 \end{bmatrix} \\
	
	\begin{bmatrix} z_2 \end{bmatrix} \\
	
	\vdots \\
	
	\begin{bmatrix} z_n \end{bmatrix} \\

\end{bmatrix}
$$

So, now we got z matrix that is a fixed size across t and micro universe. That we can read and analyze it easily what model's belief is now.

### 4. What I think actual z should be? (future direction)

I don't sure that this ideas is a good approach or not. But I think eventually even if we didn't serve model opts, it will still do the same thing at the end. 

My secondary is letting {F_0, F_1, ..., F_n} be model weight, mean to the model have to define itself what F_0 should be in this world, and how it have to update it from experiment. It's a another type of $h_t$ which I will call it $b_t$. This $b_t$ will change on t too, depend on how model belief that which F_n should be.

But there are a problem.  It's more harder to detect why model fail or how we analyze model. The F_n that learn along with experiment is similar to how human learn so much. Human didn't born with final basis law formular of the world, we invent and update it ourself. But for first version I will use only the fixed F_n from basis law, like the model born with science book that write all accurate universe basic law, then watch how it can use it to explain and create complex Y function or not.

---

## 4. Define more simplify the model and h_t

List the previous mistake or problem:
1. $h_t$ and $z$ confound confound together.
2. some math notation isn't clear.
3. z with composite step making function composition explode.
4. the composite step is over engineer and making we lost a track for the question about causal structure. 
5. So many things mixed together that it's so hard to write final model formular.


### 1. Define true world (1)

Suppose X is manipulable/exogenous variables:
$$X=\{x_0,\ldots,x_{d-1}\}$$

And Y is endogenous variables:
$$Y=\{y_0,\ldots,y_{m-1}\}$$
  
Define a topological ordering for Y:
$$y_0,\ldots,y_{m-1}$$
Which each $y_i$ have only:
$$y_i = f_{c_i}(P_i), \quad c_i \in F$$

while select parent for $y_i$ only from:
$$P_i = \text{parent } y_i, \quad P_i \in X \cup \{y_0,\ldots,y_{i-1}\}$$

This topology have proven that Y is DAG guaranteed. (Because each Y depends on earlier variables. $y_i$ can use only another $y_j$ only when $i > j$. It means to that there are acyclicity)

### 2. The true world example

For instance:
$$S = \{0, 1\}, \quad F = \{ AND, OR, NOT \}, \quad X = \{x_0, x_1, x_2, x_3\}, \quad Y = \{y_0, y_1, y_2, y_3\}$$

And suppose there is
$$y_0 = AND(x_0, x_1)$$
$$y_1 = NOT(x_2) $$
$$y_2 = OR(y0, y1)$$
$$y3 = AND(y_2, x3)$$
That we can make:
$$y_3​=AND(OR(AND(x_0​,x_1​),NOT(x_2​)),x_3​)$$

That can make multi-step composition without a_1, a_2, or composite step. Moreover, we have proven that the world generate will always be DAG.

### 4. Define true world (2)

The true world $W$ is:
$$W = \{ (c_i, P_i) \}_{i=0}^{m-1}$$
Where:
$$c_i \in F, \quad c_i = \text{operator } y_i$$
$$P_i \in X \cup \{y_0,\ldots,y_{i-1}\}, \quad P_i = \text{parent } y_i$$
For example:
$$W = \{ (AND, [x_0, x_1]), (NOT, [x_2]), (OR, [y_0, y_1]), (AND, [y_2, x_3]) \}$$


### 5. The true world capability

This approach is just composite step = 1 from our previous z concept. But it changes our all problem. Before this, because we had n complex composite step per z. It make boundary complexity explode. Making we have to freeze $f_{c_i} \in F$. That is we give all world basis law to the model, then the model just have to figure out how each assemble each $y_i$.

But now with true world topology, $\text{1 } z = \text{1 } f_{c_i} = \text{1 Operator}$. it make z even clearer to analyze. This approach allows us to accelerate that plan. We can do 2 parallel experiment:
1. $f_{c_i} \in F, \quad F = \{AND, OR, NOT, \dots\}$. This is base case. We give model the world basis function, but didn't tell it which function it is. The task is to explore that model can use existing basis law to compose complex $y_i$ or not.  
2. $f_{c_i} \in G, \quad G = \{ \text{trainable weight }\theta \}, \quad G \approx F, \quad F = \{AND, OR, NOT, \dots\}$. This is the main direction. We didn't give model anything. And model have to find itself what casual structure across n micro universe is. The task is to explore that model can find those basis law itself while use it to compose complex $y_i$ or not. And there are separate to 2 depth:
	1. $G = \{ \text{trainable weight }\theta \}$ that is fixed weight across micro universe. It's the causal law structure that model can use anywhere in $W$. And those law didn't update along with belief.
	2. $G = \{ \text{trainable weight }\theta \}$ and $G_{t+1} = f(G_t, h_t)$ that $G$ still keep minimum instruction ($G_0$) that model can start it anywhere in $W$, But the model can those generated basis function more freely. Such as the $G_0$ may keep simple knowledge how to do simple math (Only plus operator). Then on $W_{137}$ (world 137), there are so heavy at nD shifting. The model can use rough causal structure of simple math $G_0$ update to  $G_1$ that more closer to the world law $F$

But  now we will live on only $f_{c_i} \in F, \quad F = \{AND, OR, NOT, \dots\}$ to prove that it's possible to make the model.

### 4. Define action and observation format

The action $a$ will do select to do from only set $X$, where $a_t = x_t$. For example:

The model select:
$$a_t = [0, 1, 1, 0]$$
 Than mean:
$$do(x_0=0, x_1=1, x_2=1, x_3=0)$$
And the environment $W$ return:
$$o_t = [y_0, y_1, \dots,y_{m-1}]$$
Such as:
$$o_t = [0, 0, 0, 1]$$

### 5. Define history and policy

The raw history $H_t$ keep all experiment (action, observation):
$$H_t = \{(a_0, o_0), (a_1, o_1), \dots, (a_{t-1}, o_{t-1})\}$$
Where:
$$a_t = \pi(H_t)$$

But we interest in fixed bandwidth. So we create:
$$h_t = \phi(H_t) = U_\theta(h_{t-1}, a_{t-1}, o_{t-1})$$
With update rule:
$$h_{t+1} = U_\theta(h_{t-1}, a_{t-1}, o_{t-1})$$
($U$ recursively from old experiment is equivalent to $\phi$)

Where:
$$p(W \mid h_t) \approx p(W \mid H_t)$$


Therefore, we can rewrite $a_t$ to:
$$a_t\sim\pi_\psi(a\mid h_t)$$

Then we may have external action mask $M_t$ where:
$$a_t\sim\pi_\psi(a\mid h_t, M_t)$$

### 6. Define z

I will separate $z_t$ clearly from $h_t$ by:
1. $h_t$ = The actual latent brain state that model use
2. $z_t$ = Take that brain state and decode it to readable format about what it believe the world to be like

Therefore:
$$z_t=D_\omega(h_t)$$

It get approximate posterior:
$$q_\omega(W\mid h_t)$$

And get Bayesian posterior of actual world:
$$b_t(W) = p(W \mid H_t)$$

Which it's possible to compute. So finally, we want:
$$q_\omega(W\mid h_t) \approx p(W\mid H_t)$$

### 7. The $h_t$ slots discard and new concept $e_i$

List the mistake and problem:
1. First concepts $h_t$ slot was created when the $z_t$ didn't born yet. So the old concept $h_t$ and $z_t$ was confound.
2. The $h_t \approx \phi(H_t)$ Which $H_t = \{(a_0, o_0), (a_1, o_1), ..., (a_{t-1}), o_{t-1} \}$. The new $h_t$ represent all world experiment information. While old $h_t$ slots represent the belief of $y_i$ function. It's different at all.
3. If we use $h_t$ slots, it can cause inductive bias to the model that belief can exactly separate to n slots. Which it's wrong. For instance, $y_0 = f(x)$ and $y_1 = g(y_2)$. If $y_0$ changes, model have to update its belief to $y_2$ too.
4. $h_t$ slots may not a minimal sufficient structure.

Therefor, the importance of the $h_t$ slots is reduced. Now we use one single chunk $h_t$:
$$h_t \in R^d \quad h_{t+1} = U_\theta(h_t, a_t, o_t)$$
Then query $h_t$ to $z_t$ to answer what its belief about $y_i$


But $h_t$ now still didn't have $y_i$ entry. So we create one-hot vector $q_i$, where:
$$e_i=\text{Embedding(i)}$$
Such as:
$$e_0 = [1, 0, 0] \quad e_2 = [0, 1, 0] \quad e_3=[0, 0, 1]$$
Then:
$$z_t^i=D_\omega(h_t, e_i)$$
So $e_i$ just mean mean observable channel i from all history $h_t$


### 8. The $h_t$ and $z_t$ connection

The true world is:
$$W = \{ (c_i, P_i) \}_{i=0}^{m-1} $$
$$c_i \in F \quad c_i = \text{operator } y_i \quad$$
$$P_i \in X \cup \{y_0,\ldots,y_{i-1}\}, \quad P_i = \text{parent } y_i$$

The $z_t^i$ is a output logic for one $(c_i, P_i)$:
$$z_t^i = [\ell^{operator}_i, \ell^{parents}_i]$$
Then:
$$q_\omega(c_i\mid h_t,e_i) = softmax(\ell^{operator}_i)$$
and
$$q_\omega(P_i\mid c_i,h_t,e_i) = \operatorname{softmax}_{P\in\mathcal P_i(c_i)} (\ell_{i,P}^{parent})$$

The $z_t$ is just readable marginal belief, not a memory itself.


### 9. The new $h_t$ slots concept:

I didn't throw out all $h_t$ slots. I just said that those slot shouldn't represent each $y_i$ itself. On the other hand, $h_t$ should represent something about separatable history or sparsely connected history.

We can use:
$$h_t = [ g_t, s_t^0, , s_t^1, \dots ]$$
Where:
- $g_t$ = global joint memory
- $s_t^1$ = local node memory

It can used to scale model when the world complexity increase. But now I will stay in only $h_t \in R^n$ and $q_i = \text{Embedding(i)}$ first.


### 10. Final prediction loss

After all experiment budget T, we randomly select a query q. Such as:
$$q= do(X = [1, 0, 1, 1])$$

While actual $o$ is:
$$o_q = [y_0, y_1, \dots] \quad o_q \in \{0, 1 \}^n$$

Then let's model predict probability $\hat o$, where:
$$\hat o_q = R_\eta(h_T, q) \quad \hat o_q \in [0, 1]^n \subset R^n$$


Then define loss function using $BCE$:
$$\mathcal{L}_{pred} = -\log p(o_q\mid h_T,q)$$
Where:
$$p(o_q\mid h_T,q) = \prod_i p(y_i\mid h_T,q)$$
Therefor:
$$\mathcal{L}_{pred} =-\log p(o_q\mid h_T,q) = -\sum_i\log p(y_i\mid h_T,q)$$


And then in 1 world we have:
$$|\mathcal Q| = \{ q_0, q_1, \dots, q_k \}$$

We may not select all possible q to train the model. Instead, we random it to $Q_{test}$:
$$|\mathcal Q| = \text{all possible query from X}$$
$$\mathcal Q_{test} \subseteq \mathcal Q$$
Therefor:
$$\mathcal{L}_{pred} = \frac{1}{|\mathcal Q_{test}|} \sum_{q \in \mathcal Q_{test}} -\log p(o_{q}\mid h_T,q)  $$


### 11. The Boolean space strengths

Because now we're in Boolean space. Where:
$$S = \{ 0, 1 \}$$

This making full analyze probably is possible under $h_T$. We can compute ideal predictor:
$$o_q \in \{0, 1 \}^n \quad
\xrightarrow{\text{boolean analysis}}  \quad
p(o_q \mid h_T, q) \in [0, 1]^n \subset R^n
$$

This analysis can use to improve $\mathcal L_{pred}$ to more precise in the case that $h_T$ didn't have enough information to guess $\hat o$. Such as when $p(o_q = 1 \mid h_T, q) = 0.5$, eventually no more parameter or optimizer. The $p(o_q = 1 \mid h_T, q)$ have maximum information at 0.5. It's epistemic uncertainty in information $h_T$.

Or use this ideal predictor to analyze model learning curve. We can see exactly how model reduce uncertainty.


### 12. Full work flow

Generate true world:
$$W = \{ (c_i, P_i) \}_{i=0}^{m-1}$$

Initialize:
$$h_0 = h_{prior}$$

Each experiment:
$$a_t\sim\pi_\psi(a\mid h_t)$$
$$o_t=\mathcal E(W,a_t)$$
$$h_{t+1} = U_\theta(h_t,a_t,o_t)$$

Interpretable belief:
$$e_i=\text{Embedding(i)}$$
$$z_t^i=D_\omega(h_t, e_i)$$

After T experiment:
$$|\mathcal Q| = \text{all possible query from X} \quad \mathcal Q_{test} \subseteq \mathcal Q \quad q \in \mathcal Q_{test}$$
$$\hat o_q = R_\eta(h_T, q)$$
$$\mathcal{L}_{pred} = \frac{1}{|\mathcal Q_{test}|} \sum_{q \in \mathcal Q_{test}} -\log p(o_{q}\mid h_T,q)  $$
Where:
$$p(W \mid h_t) \approx p(W \mid H_t)$$

That $p(W)$ mean to the probability that current world on mathematic. But we interest in world its structure. Because the $W$ also represent $\{ (c_i, P_i) \}_{i=0}^{m-1}$ relation inside. The generated $w_1$ may be all equivalent relation to $w_{137}$. 

So careful a bit. The $p(W)$ is really mean to probability of current world by math. We can use world id in rough approximation or training. But the main direction is world that have distinct relation shape. 

### 13. The causal structure approach

As you see above, my design isn't casual structure much. The reason I didn't add this part right now is I'm still have no base line yet. 

So to make this $W$ causal, we just add one more rule to $a_t$. From do only X:

$$a_t = do(X=[1, 0])$$
To
$$a_t = do(X=[1,0], Y=[1, 0, 0])$$


The show the mechanism inside, I suppose:
$$y_0 = AND(x_0, x_1)$$
$$y_1 = NOT(y_0)$$
$$y_2=NOT(y_1)$$
$$y_3 = AND(x_0, x_1)$$
Get the relation:

$$(x_0, x_1) \rightarrow y_0 \rightarrow y_1 \rightarrow y_2$$
$$(x_0, x_1) \rightarrow y_3$$

At old $a_t$ that have only $do(X)$. Nothing happen yet:
$$a_t = do(X=[1,0]) \ \rightarrow \ y_0= 0 ,\ y_1=1, \ y_2=0, y_3=0$$

But For new $a_t$ with $do(X, Y)$. The do(Y) will override $y_i$ answer:
$$a_t = do(X=[1,0], y_0=1) \ \rightarrow \ y_0 = 1 \text{ (AND(1,0)=0, but was override to 1)}$$

Then the next node that connected with $y_0$ will be override too. The $y_1$ and $y_2$ will go: 
$$\ y_1= 0 \text{ ( affect by } y_0 \text{ that was override)}, \ y_2=0 \text{ ( affect by } y_1 \text{)}$$

While the other node that isolate from $y_0$ is stay still. The $y_3$ is same:
$$a_t = do(X=[1,0], y_0=1) \ \rightarrow \ y_3 = AND(x_0, x_1) = 0 $$

For more clear picture:
$$a_t = do(X=[1,0]) \ \rightarrow \ y_0= 0 ,\ y_1=1, \ y_2=0, \quad y_3=0$$
$$a_t = do(X=[1,0], y_0=1) \ \rightarrow \ y_0 = 1, \ y_1 = 0, \ y_2=1, \quad y_3 = 0 $$

This approach will make actual causal structure from:
$$\text{Change X} \rightarrow \text{change all Y}$$
To:
$$\text{Change } y_i \rightarrow \text{change all } y_j \text{ where } y_j \text{ is connected } y_i$$
Such as:
$$X \rightarrow y_0 \rightarrow y_1 \rightarrow y_2 \rightarrow y_3$$
$$y_1 \rightarrow y_4 \rightarrow y_5 $$

But this approach is a bit complex to use now. So I decide to make simple $a_t$ with only $do(X)$ first. Then when I have all understand ground, I will go deeper to $do(X, Y)$.

---

## Next part is [[stage-2-model-and-implementation]]