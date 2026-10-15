/* ^ticket(58): dominator tree of a heap snapshot graph (Semi-NCA,
   Georgiadis), and each node's retained bytes, total and new.
   in:  first.bin (int64 N+1), to.bin (int32 E), keep.bin (uint8 E: edge
        counts, i.e. not weak), self.bin (double N), new.bin (uint8 N)
   out: idom.bin (int32 N, node index, -1 unreached), ret.bin, retnew.bin
        (double N)
   usage: dom <dir> <N> <E> */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
static void *rd(const char *dir, const char *f, size_t n) {
  char p[4096]; snprintf(p, sizeof p, "%s/%s", dir, f);
  FILE *fp = fopen(p, "rb"); if (!fp) { perror(p); exit(1); }
  void *b = malloc(n); if (fread(b, 1, n, fp) != n) { fprintf(stderr, "short %s\n", p); exit(1); }
  fclose(fp); return b;
}
static void wr(const char *dir, const char *f, void *b, size_t n) {
  char p[4096]; snprintf(p, sizeof p, "%s/%s", dir, f);
  FILE *fp = fopen(p, "wb"); fwrite(b, 1, n, fp); fclose(fp);
}
int main(int argc, char **argv) {
  const char *dir = argv[1]; long N = atol(argv[2]), E = atol(argv[3]);
  int64_t *first = rd(dir, "first.bin", (N + 1) * 8);
  int32_t *to = rd(dir, "to.bin", E * 4);
  uint8_t *keep = rd(dir, "keep.bin", E);
  double *self = rd(dir, "self.bin", N * 8);
  uint8_t *isnew = rd(dir, "new.bin", N);
  /* DFS preorder from node 0 */
  int32_t *dfn = malloc(N * 4), *vert = malloc(N * 4), *par = malloc(N * 4);
  for (long i = 0; i < N; i++) dfn[i] = -1;
  int32_t *stk = malloc(N * 4); int64_t *nxt = malloc(N * 8); long sp = 0, n = 0;
  dfn[0] = n; vert[n] = 0; par[n] = 0; n++; stk[sp] = 0; nxt[sp] = first[0]; sp++;
  while (sp) {
    int32_t v = stk[sp - 1]; int64_t e = nxt[sp - 1];
    while (e < first[v + 1] && (!keep[e] || dfn[to[e]] >= 0)) e++;
    if (e == first[v + 1]) { sp--; continue; }
    nxt[sp - 1] = e + 1;
    int32_t w = to[e]; dfn[w] = n; vert[n] = w; par[n] = dfn[v]; n++;
    stk[sp] = w; nxt[sp] = first[w]; sp++;
  }
  free(stk); free(nxt);
  fprintf(stderr, "dfs: %ld of %ld reached\n", n, N);
  /* predecessors, in dfs numbers, of reached nodes */
  int64_t *pf = calloc(n + 1, 8);
  for (long v = 0; v < N; v++) if (dfn[v] >= 0)
    for (int64_t e = first[v]; e < first[v + 1]; e++) if (keep[e] && dfn[to[e]] >= 0) pf[dfn[to[e]] + 1]++;
  for (long i = 0; i < n; i++) pf[i + 1] += pf[i];
  int32_t *pr = malloc(pf[n] * 4); int64_t *fill = malloc(n * 8);
  for (long i = 0; i < n; i++) fill[i] = pf[i];
  for (long v = 0; v < N; v++) if (dfn[v] >= 0)
    for (int64_t e = first[v]; e < first[v + 1]; e++) if (keep[e] && dfn[to[e]] >= 0) pr[fill[dfn[to[e]]]++] = dfn[v];
  free(fill); free(first); free(to); free(keep);
  /* semidominators with link-eval (path compression), in dfs numbers */
  int32_t *semi = malloc(n * 4), *label = malloc(n * 4), *anc = malloc(n * 4), *idom = malloc(n * 4);
  for (long i = 0; i < n; i++) { semi[i] = i; label[i] = i; anc[i] = -1; }
  int32_t *path = malloc(n * 4);
  for (long w = n - 1; w >= 1; w--) {
    for (int64_t k = pf[w]; k < pf[w + 1]; k++) {
      int32_t v = pr[k], u;
      if (anc[v] < 0) u = v;
      else {
        long m = 0; int32_t x = v;
        while (anc[x] >= 0 && anc[anc[x]] >= 0) { path[m++] = x; x = anc[x]; }
        for (long q = m - 1; q >= 0; q--) {
          int32_t y = path[q];
          if (semi[label[anc[y]]] < semi[label[y]]) label[y] = label[anc[y]];
          anc[y] = anc[anc[y]];
        }
        u = label[v];
      }
      if (semi[u] < semi[w]) semi[w] = semi[u];
    }
    anc[w] = par[w];
  }
  idom[0] = 0;
  for (long w = 1; w < n; w++) { int32_t x = par[w]; while (x > semi[w]) x = idom[x]; idom[w] = x; }
  /* retained bytes, children before parents (reverse preorder) */
  double *ret = calloc(N, 8), *retn = calloc(N, 8);
  for (long w = n - 1; w >= 0; w--) {
    int32_t v = vert[w]; ret[v] += self[v]; if (isnew[v]) retn[v] += self[v];
    if (w) { int32_t p = vert[idom[w]]; ret[p] += ret[v]; retn[p] += retn[v]; }
  }
  int32_t *idn = malloc(N * 4);
  for (long v = 0; v < N; v++) idn[v] = dfn[v] >= 0 ? vert[idom[dfn[v]]] : -1;
  wr(dir, "idom.bin", idn, N * 4); wr(dir, "ret.bin", ret, N * 8); wr(dir, "retnew.bin", retn, N * 8);
  fprintf(stderr, "root retains %.1f MB, new %.1f MB\n", ret[0] / 1048576, retn[0] / 1048576);
  return 0;
}
