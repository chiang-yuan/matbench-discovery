<script lang="ts">
  import { afterNavigate, goto } from '$app/navigation'
  import { page } from '$app/stores'
  import { Footer, Nav } from '$lib'
  import { repository } from '$site/package.json'
  import { CmdPalette } from 'svelte-multiselect'
  import Toc from 'svelte-toc'
  import { CopyButton, GitHubCorner, PrevNext } from 'svelte-zoo'
  import '../app.css'

  const routes = Object.keys(import.meta.glob(`./*/+page.{svelte,md}`)).map(
    (filename) => `/` + filename.split(`/`)[1]
  )

  $: url = $page.url.pathname
  $: headingSelector = `main :is(${
    { '/api': `h1, ` }[url] ?? ``
  }h2, h3, h4):not(.toc-exclude)`

  $: description = {
    '/': `Benchmarking machine learning energy models for materials discovery.`,
    '/data': `Details about provenance, chemistry and energies in the benchmark's train and test set.`,
    '/data/tmi': `Too much information on the benchmark's data.`,
    '/api': `API docs for the Matbench Discovery PyPI package.`,
    '/contribute': `Steps for contributing a new model to the benchmark.`,
    '/models': `Details on each model sortable by metrics.`,
    '/preprint': `The preprint released with the Matbench Discovery benchmark.`,
    '/preprint/iclr-ml4mat': `Extended abstract submitted to the ICLR ML4Materials workshop.`,
  }[url ?? ``]
  if (url && !description) console.warn(`No description for url=${url}`)
  $: title = url == `/` ? `` : `${url} • `

  const actions = Object.keys(import.meta.glob(`./**/+page.{svelte,md}`)).map(
    (filename) => {
      const parts = filename.split(`/`).filter((part) => !part.startsWith(`(`)) // remove hidden route segments
      const route = `/${parts.slice(1, -1).join(`/`)}`

      return { label: route, action: () => goto(route) }
    }
  )
  afterNavigate(({ to }) => {
    if (to?.route.id == `/models`) {
      document.documentElement.style.setProperty(`--main-max-width`, `90em`)
    } else {
      document.documentElement.style.setProperty(`--main-max-width`, `50em`)
    }

    for (const node of document.querySelectorAll(`pre > code`)) {
      // skip if <pre> already contains a button (presumably for copy)
      const pre = node.parentElement
      if (!pre || pre.querySelector(`button`)) continue

      new CopyButton({
        target: pre,
        props: {
          content: node.textContent ?? ``,
          style: `position: absolute; top: 1ex; right: 1ex;`,
        },
      })
    }
  })
</script>

<CmdPalette {actions} placeholder="Go to..." />

<svelte:head>
  <title>{title}Matbench Discovery</title>
  <meta name="description" content={description} />
</svelte:head>

{#if url !== `/models`}
  <Toc {headingSelector} breakpoint={1250} minItems={3} />
{/if}

<GitHubCorner href={repository} />

<main>
  <Nav routes={[[`/home`, `/`], ...routes.filter((route) => route != `/changelog`)]} />

  <slot />

  <PrevNext
    items={routes}
    current="/{url?.split(`/`)[1]}"
    style="margin: 4em auto 1em; max-width: 60em;"
  >
    <a slot="next" let:item={href} {href} class="link">{href} &raquo;</a>
    <a slot="prev" let:item={href} {href} class="link">&laquo; {href}</a>
  </PrevNext>
</main>

<Footer />

<style>
  a[href='/'] {
    font-size: 14pt;
    background-color: rgba(255, 255, 255, 0.1);
    padding: 1pt 5pt;
    border-radius: 3pt;
    transition: 0.2s;
    width: max-content;
    box-sizing: border-box;
    margin: 1em 0 0 1em;
  }
  @media (min-width: 900px) {
    a[href='/'] {
      position: absolute;
      top: 1em;
      left: 1em;
    }
  }
  a[href='/']:hover {
    background-color: rgba(255, 255, 255, 0.2);
  }
</style>
