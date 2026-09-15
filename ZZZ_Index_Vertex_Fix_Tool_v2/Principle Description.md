# 原理说明 / How It Works

绝区零 索引与顶点修复工具 v2 · ZZZ Index & Vertex Fix Tool v2

这份文档讲工具在背后做了什么 —— 为什么坏、怎么算出来、怎么判断该不该动手。想改它、移植到别的游戏、或者自己写一个，从这里开始。

---

## 中文

### 一、骨骼索引（VGX）

**数据结构。** `blend.buf` 每顶点 32 字节：前 16 字节是 4 个 float 蒙皮权重，后 16 字节是 4 个 uint32 骨骼索引。索引是骨骼数组的下标，权重决定影响多少。

**为什么坏。** 游戏更新后骨骼数组的顺序会变（新增、合并、重排）。同一个关节换了编号，而 mod 里烘焙的是旧编号 —— 顶点被拉去跟错的骨头走，表现出来就是腿弯、塌陷、扭曲。贴图不受影响，因为贴图和骨骼无关。

**怎么推出来。** mod 网格通常是游戏原网格的细分版或改造版，顶点位置大面积重合，位置就是配对的锚点。

1. 把 mod 顶点灌进空间哈希网格，格子边长 = 配对半径 `0.01` 游戏单位。取格子用 `floor` 而不是 `int()` —— 负坐标上 `int()` 是朝零截断，跨 0 的那个格子会被撑成两倍宽，边界外一个半径内的顶点就漏了。
2. 每个游戏顶点查周围 ±1 格（格子边长等于半径，所以 ±1 足够），收集半径内的 mod 顶点，最多取最近 6 个。
3. 每一对顶点比较各自的 4 个槽位：两边都按权重降序排，逐位对齐；槽位权重 ≥ `0.01` 且两边权重差 ≤ `0.05` 时，投一票 `mod 索引 → 游戏索引`。
4. 把所有票按票数从高到低贪心落定，一个旧索引只允许对上一个新索引（一一对应），先到先得。
5. 结果过滤：配到的游戏顶点少于 `5%` → 判为不是同一套网格，整条跳过；映射全是恒等 → 已经是对的，跳过；票数少于 `20` 的条目标黄提醒人工复核。

**为什么用权重做判据。** 位置配对本身有误差（同一个骨架下相邻顶点可能靠得很近），权重是第二重指纹：位置几乎重合、同时某一槽位的权重也一致的两条顶点，基本可以断定是同一根骨骼。

**输出。** 一张 `旧索引 → 新索引` 表，重写 `blend.buf` 里每顶点后 16 字节的 4 个 uint32，权重原样不动。

**实测。** 琉音身体，mod 134133 顶点 / 游戏 15715 顶点：配到 74% 的游戏顶点，最近距离中位数 0.0042（大约是身高的 0.4%）。这个精度足够定骨骼。

### 二、顶点格式（texcoord）

**布局。** mod 在 ini 里把缓冲分三条流绑给游戏：`vb0` 位置（stride 40）、`vb1` texcoord、`vb2` blend（stride 32）。texcoord 那条流里装的是这个网格需要的顶点属性 —— COLOR 加上 TEXCOORD0..N，顺序就是内存里的顺序。

**为什么坏。** 3.1 → 3.2 更新里，部分网格的顶点 COLOR 从 `R8G8B8A8_UNORM`（4 字节）改成了 `R32G32B32A32_FLOAT`（16 字节）。每顶点从 36 字节变成 48 字节。mod 的 buf 还是老布局、ini 里还写着 `stride = 36`，游戏按新布局去读，每顶点的边界就整体错位 —— 贴图糊成一片、铺得满身都是。

**怎么转。** 逐顶点重排：把 COLOR 那 4 个字节按 `b / 255.0` 展开成 4 个 float，后面所有块原样搬过去，再把 ini 里的 stride 改成新值。颜色块是唯二需要做数值换算的地方（`4B` ↔ `4f`、`4B` ↔ `4e` 之间是 0-255 与 0.0-1.0 的换算），其余块是原样复制字节。

**怎么判断该不该动手。** 猜错格式去改 buf 会把好文件毁掉，所以这里有三重确认：

1. **目标布局从 dump 的元素表来** —— 读的是游戏当前状态，不是写死的常量。
2. **顶点数**：先按 blend 节的 hash 找到 blend 缓冲（大小 ÷ 32），这条不依赖文件命名；找不到就退回同名的 `*Blend.buf` / `*Position.buf`；再不行才按 buf 大小能否整除来反推。
3. **每顶点字节数 = buf 大小 ÷ 顶点数**：等于旧布局就转，等于新布局就跳过（已经修过），两个都不等就打印提示然后跳过 —— 绝不猜。

**旧布局是倒推出来的。** 把新布局里的某个 `4f` 块缩成 `4B` 或 `4e`，看哪个候选算出来的字节数等于 buf 的实际值。COLOR 块在 texcoord 里排第一，所以取第一个能凑上的候选。

### 三、通用脸部修复（模式 2）

同一种变化，不需要参照：COLOR 4 字节 → 4 个 float，36 → 48 字节/顶点。认的是内嵌在代码里的一张名单（53 个网格 / 46 个角色），hash 取 3.1 → 3.2 更新日志里"更新后"的 texcoord hash。命中名单的节，才动它 `vb1` 绑的那个 buf（和 stride）。骨骼索引不管。

### 四、hash 是干什么的

dump 的 `hash.json` 给的是 `texcoord_vb` / `blend_vb` / `position_vb` / `ib` 四个值，都是游戏当前版本的 hash。ini 里 `[TextureOverride...]` 节的 `hash =` 就是该缓冲或索引的 hash，工具靠它定位 `vb0` / `vb1` / `vb2` 实际绑的是哪个文件。

一组参照 = `Dump\` 里的一个文件夹（一个网格）。同一时刻只有一组生效：mod 的 ini 里必须至少命中该组的一个 hash，整包才处理 —— 否则什么都不动。这条闸门是为了防止把 A 角色的修复套到 B 角色身上：各组的 hash 完全不同，跨组命中基本不可能。

hash 是旧版的 mod 匹配不上任何一组，所以要先更新 hash。

### 五、已知局限

- 位置对不上就推不出骨骼映射：模型被整体缩放、大幅改形，或者 mod 只覆盖游戏网格的一小块时，配对率会掉下来（低于 5% 直接跳过）。
- 票数少的条目可能配错，工具会标出来，但需要人工判断。
- 映射用贪心一一对应，不保证全局最优。
- 只认 4 权重 / 32 字节的 blend 布局；别的权重数（比如 8 权重）不处理。
- texcoord 只处理"元素块等宽重排"这一类变化；元素数量或语义本身变了，判断不出来就跳过。

---

## English

### 1. Bone indices (VGX)

**The data.** `blend.buf` is 32 bytes per vertex: 16 bytes of four float skin weights, then 16 bytes of four uint32 bone indices. An index is a position in the skeleton's bone array; the weight says how much that bone pulls.

**Why it breaks.** Game updates reorder the bone array (bones get added, merged, shuffled). A joint keeps its meaning but changes its number, while the mod still carries the old numbers baked in. Vertices follow the wrong bone: bent legs, collapse, twisting. Textures are unaffected — they have nothing to do with the skeleton.

**How the tool derives the mapping.** A mod mesh is usually a subdivided or edited copy of the game's mesh, so vertex positions overlap heavily. Position is the anchor:

1. Mod vertices go into a spatial hash grid with the cell size equal to the pairing radius, `0.01` game units. Cell lookup uses `floor`, not `int()` — `int()` truncates toward zero, which doubles the width of the cell straddling zero and drops vertices that are within one radius outside it.
2. For each game vertex, look at the ±1 neighbourhood (cell size equals radius, so ±1 is enough), collect mod vertices inside the radius, keep at most the 6 nearest.
3. For each pair, compare the four weight slots: both sides sorted by weight descending and zipped positionally. When a slot's weight is ≥ `0.01` and the two weights differ by ≤ `0.05`, cast one vote `mod index → game index`.
4. Resolve all votes greedily, highest count first, with a one-to-one constraint: an old index may map to exactly one new index.
5. Filter the result: fewer than `5%` of game vertices matched → not the same mesh, skip; identity mapping → already correct, skip; entries with fewer than `20` votes are flagged for manual review.

**Why weights are the second signal.** Position pairing has inherent noise — vertices next to each other on the same skeleton sit close together. Weights disambiguate: two vertices at nearly the same position *and* with a matching weight in a slot are almost certainly bound to the same bone.

**Output.** A `old → new` table; the tool rewrites the last 16 bytes (four uint32) of every vertex in `blend.buf` and leaves the weights untouched.

**Measured.** Dialyn body, mod 134133 vertices vs game 15715: 74% of game vertices matched, median nearest distance 0.0042 — about 0.4% of body height. That is far below any bone spacing.

### 2. Vertex format (texcoord)

**The layout.** The ini binds the mod's buffers as three streams: `vb0` position (stride 40), `vb1` texcoord, `vb2` blend (stride 32). The texcoord stream carries the attributes that mesh needs from the texcoord input — COLOR followed by TEXCOORD0..N, in memory order.

**Why it breaks.** In the 3.1 → 3.2 update the game changed the vertex COLOR element of some meshes from `R8G8B8A8_UNORM` (4 bytes) to `R32G32B32A32_FLOAT` (16 bytes) — 36 → 48 bytes per vertex. The mod's buf still has the old layout and the ini still declares `stride = 36`. The game reads it with the new layout, every vertex boundary shifts, and the texture is smeared across the model.

**The conversion.** Per vertex: expand the 4 COLOR bytes into 4 floats via `b / 255.0`, copy every following block verbatim, then rewrite the stride in the ini. COLOR is the only block that needs a value conversion (`4B` ↔ `4f` and `4B` ↔ `4e` convert between 0-255 and 0.0-1.0); everything else is a byte-for-byte copy.

**Deciding whether to touch a file.** Rewriting a buf with the wrong layout assumption destroys a good file, so the tool confirms three times:

1. **The target layout comes from the dump's element table** — the game's live state, never a hard-coded constant.
2. **Vertex count**: first from the blend buffer located by its section hash (size ÷ 32), which does not depend on file naming; then from same-named `*Blend.buf` / `*Position.buf`; only then by testing whether the buf size divides evenly.
3. **Bytes per vertex = buf size ÷ vertex count**: equal to the old layout → convert; equal to the new layout → skip (already fixed); neither → print a note and skip. It never guesses.

**The old layout is inferred, not assumed.** Shrink one `4f` block of the new layout to `4B` or `4e` and see which candidate reproduces the buf's actual per-vertex size. COLOR is the first element of the texcoord stream, so the first fitting candidate wins.

### 3. Universal Face Fix (mode 2)

One specific change, no reference needed: COLOR 4 bytes → 4 floats, 36 → 48 bytes per vertex. It works from a list embedded in the code (53 meshes / 46 characters), keyed by the texcoord hash from the "after" side of the 3.1 → 3.2 change log. A section matching the list gets its `vb1` buf (and the stride) rewritten. Bone indices are not touched.

### 4. What the hashes are for

The dump's `hash.json` carries `texcoord_vb` / `blend_vb` / `position_vb` / `ib` — all current game values. A `hash =` line inside a `[TextureOverride...]` section is the hash of that buffer or index buffer, and the tool uses it to find which file the section's `vb0` / `vb1` / `vb2` actually binds.

One reference set = one folder in `Dump\` (one mesh). Only one set is active at a time, and the mod's ini must hit at least one hash of that set or the whole folder is left alone. That gate prevents fixing character A with character B's data: the sets share no hashes.

A mod whose hashes are from an older game version matches nothing — hence "update the hashes first".

### 5. Known limits

- No position overlap, no mapping: a mesh scaled as a whole, heavily reshaped, or covering only a small part of the game mesh drops below the 5% match threshold and is skipped.
- Low-vote entries can be wrong. The tool flags them; judging them is on you.
- The mapping is a greedy one-to-one assignment, not a global optimum.
- Only the 4-weight / 32-byte blend layout is handled. Other weight counts (8 weights, for instance) are not.
- For texcoord, only equal-width re-packing of element blocks is handled. If the element count or semantics themselves changed, the tool cannot tell and skips.
