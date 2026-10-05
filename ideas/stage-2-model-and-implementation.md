> This draft is writing about the actual implementation on top step 1 concept. Each topic is arranged chronologically, following the experiments conducted in `src/stage-2/`.

## 1. Freeze mathematical contract

Now I will freeze mathematical contract:
$$S=\{0,1\},\qquad F=\{\text{AND},\text{OR},\text{NOT}\}$$
$$X=\{x_0,\dots,x_{d-1}\},\qquad Y=\{y_0,\dots,y_{m-1}\}$$
By:
$$ y_i=f_{c_i}(P_i) $$
$$ P_i\subseteq X\cup\{y_0,\dots,y_{i-1}\}. $$

Then:
$$ a_t = do(X=a_t)\in\{0,1\}^{d} $$
$$
 o_t=\mathcal E(W,a_t)\in\{0,1\}^{m}. 
$$
And:
$$h_{t+1}=U_\theta(h_t,a_t,o_t)$$

By using:
$$d=4 \quad \text{ and } \quad m=4$$

---
## 2. Exact world analysis

We have hypothesis space for every world from world-generation contract:
$$\Omega=\{W_1,W_2,\ldots,W_N\}$$

Suppose that
$$W \in \Omega$$


Suppose history at t is
$$H_t​=\{(a_0​,o_0​),\dots,(a_{t−1}​,o_{t−1​})\}$$

Then we have fixed function:
$$F=\{\text{AND},\text{OR},\text{NOT}\}$$
- $AND$ = $function: S^2 \rightarrow S$ with commutative Property
- $OR$ = $function: S^2 \rightarrow S$ with commutative Property
- $NOT$ = $function: S \rightarrow S$

Therefor, assume that node $N_i$ have parent pool size $k_i$. There have all possible hypothesis:
$$N_i = \underbrace{\binom{k_i}{2}}_{\text{AND}} + \underbrace{\binom{k_i}{2}}_{\text{OR}} + \underbrace{k_i}_{\text{NOT}}, \quad |\Omega| = \prod_{i=0}^{m-1} N_i$$
But pool size $k_i$ isn't constant, it's increase on i. Because $P_i \in X \cup \{y_0,\ldots,y_{i-1}\}$. So at $n=4$,$m=4$:
$$k_i = n + i, \quad i = [0, m-1]$$
$$N_0 = \binom{4}{2} + \binom{4}{2}+\binom{4}{1}=16$$
$$N_1 = \binom{5}{2} + \binom{5}{2}+\binom{5}{1}=25$$
$$N_2 = \binom{6}{2} + \binom{6}{2}+\binom{6}{1}=36$$
$$N_3 = \binom{7}{2} + \binom{7}{2}+\binom{7}{1}=49$$
So:
$$|\Omega| = \prod_{i=0}^{m-1} N_i = 705,600  \approx 2^{19.4}$$
But It's still not count some relation equivalent like $AND(A, B) = AND(AND(A, B), A))$ or $A = NOT(NOT(A)$). So we should careful a bit:

---
## 3. Equivalence class

The world analysis above can prevent only commutative property. But the relation equivalence still live there. For example:
$$y_0 = AND(A, B)$$
$$y_1 = AND(y_0, A) = AND(y_0, B)$$
Or:
$$A = NOT(NOT(A)) = AND(A, OR(B, NOT(B)))$$

Therefor, I define equivalence class:
$$W_i \sim_{\mathcal A} W_j$$
Where $\mathcal A = action$:
$$\mathcal E(W_i,a)=\mathcal E(W_j,a) \qquad \forall a\in\mathcal A$$
$$\mathcal A_X=\{do(X=x):x\in\{0,1\}^m\}$$

With that:
$$|x| = |\{0, 1\}^4| = 2^4 = 16$$

Therefor, we have 16 the world signature (From only do(X) experiment):
$$signature_X(W) = [ \mathcal E(W,x_0), \mathcal E(W,x_1), \dots, \mathcal E(W,x_{15}) ]$$

That mean now, it's require action compute:
$$\text{action compute require} = |\Omega| \cdot |x| = 11,289,600$$


And the world signature size is:
$$|signature_X(W)| = |action| \cdot m = |x| \cdot m = 64$$
(Action = $|x|$ = 16, while observation = $|y|$ = 4 / each action)


Which mean
$$\text{signature combination} = 2^{|signature(W)|} = 2^{64}$$

That mean current $2^{19.4}$ exact world can keep in $2^{64}$  signature patten. (With 16 exact action). The current world signature space is enough to every combination of exact world. But the biggest problem we found here is equivalent class that many world can produce same signature.

---
## 4. Reprioritize causal structure  do(X,Y) approach

And because now our problem is only equivalence class. I decide to priority do(X, Y) plan higher. This pieces is a great solution to fix it.

First, increasing $m$ or $|Y|$ is able to make different equivalence class per exact world generate. But it is in-efficient, because:
$$\frac{|\Omega_{m+1}|}{|\Omega_{m}|} = (d+m)^2, \quad \frac{ |signature_X(W)_{m+1}|}{|signature_X(W)_{m}|} = \frac{m+1}{m}$$

The different rate of change between its both is so different. And if we change $m$, it mean to we have to generate whole world and recompute all probability again to prepare dataset.


So now at new plan to do(X, Y), I design 3 different stage experiment. That is:

### 1. Stage A: do(X)

$$a=do(X=x)$$
$$\text{action combination} = |S|^d = 2^4 = 16$$
$$|signature_X(W)|= |action| \cdot m = 64$$
### 2. Stage B: do(X, one Y)

$$a=do(X=x, y_i​=v)$$
Then we can select $y_i$ only from $[\text{not select}, y_i=0, y_i=1]$ where $i = m = 4$. So:
$$\text{action combination} = |S|^d \cdot (1 + 2m) = 2^4 \cdot 9 = 144$$
(The action set $y_i = 0$ is not equal action "do nothing" which is we don't set its $y_i$ at all.)

$$|signature_{XY}(W)|= |action| \cdot m = 576$$

### 3. Stage C: do(X, arity Y) 
$$a=do(X=x, Y​=y)$$
Then we can select $y_i$ only from $[\text{not select}, combination(Y)]$. So:
$$\text{action combination} = |S|^d \cdot (|S|+1)^m = 2^4 \cdot 3^4 = 1,296$$
(Each $y_i$ have only state [do nothing, set to 0, set to 1])

$$|signature_{XY}(W)|= |action| \cdot m = 5,184$$

### N. New plan approach

The current plan will do those stage A-C parallelly. Using its 3 different result compare together for deeper analysis about equivalence class consequence. 

---

## 5. Exact Bayesian oracle and posterior (1) : do(X)

Define: Posterior = what is probability of the world we live now:
$$\text{Posterior: }p(W\mid H_t)$$

Define: Oracle prediction = what is observation we think it will be:
$$\text{Oracle prediction: }p(o_q\mid H_t,q)$$

From Bayes rule, we get:
$$p(W\mid H_t) = \frac {p(H_t\mid W)p(W)} {\sum_{W'\in\Omega}p(H_t\mid W')p(W')}$$
- $p(W\mid H_t)$= Given the history H_t, what is the probability that the current world is W?
- $p(H_t\mid W)$ = If the true world is W, how likely is it that we would observe the history H_t?
- $p(W)$ = Our prior belief about world W, before seeing the current history.
- $p(H_t\mid W)p(W)$ = The unnormalized belief for world W. It combines how plausible W was before and how well W explains the observed history.
- $\sum_{W'\in\Omega} p(H_t\mid W')p(W')$ = The total probability of observing H_t across all possible worlds in \Omega. It is used to normalize the posterior so that all world probabilities sum to 1.

Therefore:
$$\frac{ p(H_t\mid W)p(W) }{ \sum_{W'\in\Omega}p(H_t\mid W')p(W') }$$
Mean to compare how well world `W` explains the observed history against how well all possible worlds in `\Omega` explain the same history.



Same case with:
$$p(W\mid H_t, a_t, o_t) = \frac {p(o_t\mid W, H_t, a_t)p(W | H_t, a_t)} {\sum_{W'\in\Omega}p(o_t\mid W', H_t,a_t)p(W' | H_t, a_t)}$$


And then we also able to update $p(W\mid H_t)$ by each experiment, Because:
$$p(W\mid \{(a_0​,o_0​),\dots,(a_{t−1}​,o_{t−1​})\}) \rightarrow p(W\mid \{(a_0​,o_0​),\dots,(a_{t−1}​,o_{t−1​}),(a_{t}​,o_{t})\})$$
$$p(W\mid H_t) \rightarrow p(W\mid H_{t+1})$$

Therefor:
$$p(W \mid H_{t+1}) = \frac {p(o_t \mid W, a_t)p(W \mid H_t)} {\sum_{W'\in\Omega}p(o_t\mid W',a_t)p(W' \mid H_t)}$$
- $p(o_t\mid W,a_t)$ = If the current world were W, how likely would it be to observe $o_t$ after performing $a_t$?
- $p(W\mid H_t)$ = Our belief in world W before seeing the new observation.
- $p(o_t\mid W,a_t)p(W\mid H_t)$ = The updated, but still unnormalized, belief in W. A world gets high weight when it was already plausible and also explains the new observation well.
- The denominator sums this quantity over every possible world, so that the new posterior sums to 1.


Then suppose that:
$$b_t(W)\equiv p(W\mid H_t)$$
We get new posterior: 
$$b_{t+1}(W) = \frac{ p(o_t\mid W,a_t)b_t(W) }{ \sum_{W'}p(o_t\mid W',a_t)b_t(W') }$$


---
## 6. Exact Bayesian oracle and posterior (2) : Computation

With that deterministic environment:
$$o=\mathcal E(W,a)$$
For 1 experiment, we get:
$$p(o_t\mid W,a_t)=
\begin{cases}
	1,&\mathcal E(W,a_t)=o_t\\
	0,&\mathcal E(W,a_t)\neq o_t
\end{cases}$$
Therefor:
$$p(W\mid H_t) \propto p(W) \prod_{k=0}^{t-1} \mathbf 1[\mathcal E(W,a_k)=o_k]$$

And then we define surviving set:
$$C_t = \left\{ W: \mathcal E(W,a_\tau)=o_\tau,\; \forall\tau<t \right\}$$
Then:
$$ p(W\mid H_t) = \begin{cases} \frac1{|C_t|},&W\in C_t\\ 0,&W\notin C_t \end{cases}$$

Under a uniform prior over all exact worlds:
$$p(W) = \frac{1}{|\Omega|}$$
With that identity:
$$\left\{ W: \mathcal E(W,a_\tau)=o_\tau,\; \forall\tau<{t+1} \right\} \subseteq \left\{ W: \mathcal E(W,a_\tau)=o_\tau,\; \forall\tau<{t} \right\}$$
$$C_{t+1} \subseteq C_{t}$$

---

## 7. Exact Bayesian oracle and posterior (3) : do(X, Y) 

The Bayes update still be the same, where:
$$b_{t+1}(W) \propto p(o_t\mid W,a_t)b_t(W)$$$$ p(W\mid H_t) = \begin{cases} \frac1{|C_t|},&W\in C_t\\ 0,&W\notin C_t \end{cases}$$

The only thing that changes is: 
$$\mathcal E(W,a)$$

For stage A (previous proves):
$$a=do(X=x)$$

For stage B:
$$a=do(X=x,y_i=v)$$

For stage C:
$$a=do(X=x,Y=y)$$

---

## 8. Exact Bayesian oracle and posterior (4) : Sequential computation

### 1. First initialize

We have no $h_0$ to separate the world. So:
$$H_0=\varnothing$$
$$C_0 = \Omega$$

By uniform prior:
$$b_0 \equiv p(W\mid H_0) = \begin{cases} \frac1{|\Omega|},&W\in C_0 \\ 0,&W\notin C_0 \end{cases}$$

Then we we compute likelihood from $o_0$:
$$p(o_0\mid W,a_0) = \begin{cases} 1,&\mathcal E(W,a_0)=o_0\\ 0,&\mathcal  (W,a_0)\neq o_0 \end{cases}$$

Getting:
$$b_1(W) = \frac{ p(o_0\mid W,a_0)b_0(W) }{ \sum_{W'}p(o_0\mid W',a_0)b_0(W') }$$
And
$$H_1 = \{(a_0, o_0)\}$$

### 2. The loop

The we filter $C_0$ set by $o_0$ experiment:
$$\text{filter } C_0 \rightarrow C_1$$
$$\text{filter } \left\{ W: \mathcal E(W,a_\tau)=o_\tau,\; \forall\tau<0 \right\} \rightarrow \left\{ W: \mathcal E(W,a_\tau)=o_\tau,\; \forall\tau<1 \right\}$$

Compute:
$$b_1 \equiv p(W\mid H_1) = \begin{cases} \frac1{|C_1|},&W\in C_1 \\ 0,&W\notin C_1 \end{cases}$$
$$p(o_1\mid W,a_1) = \begin{cases} 1,&\mathcal E(W,a_1)=o_1\\ 0,&\mathcal  (W,a_1)\neq o_1 \end{cases}$$

Getting: 
$$b_2(W) = \frac{ p(o_1\mid W,a_1)b_1(W) }{ \sum_{W'}p(o_1\mid W',a_1)b_1(W') }$$
And
$$H_2 = \{(a_0, o_0), (a_1, o_1)\}$$

