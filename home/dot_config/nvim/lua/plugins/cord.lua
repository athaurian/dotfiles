local pretty = {
  -- Programming languages
  c = "C",
  cpp = "C++",
  cs = "C#",
  java = "Java",
  kotlin = "Kotlin",
  scala = "Scala",
  groovy = "Groovy",
  clojure = "Clojure",
  lua = "Lua",
  python = "Python",
  ruby = "Ruby",
  perl = "Perl",
  php = "PHP",
  go = "Go",
  rust = "Rust",
  swift = "Swift",
  dart = "Dart",
  zig = "Zig",
  nim = "Nim",
  julia = "Julia",
  pascal = "Pascal",
  fortran = "Fortran",
  cobol = "COBOL",
  d = "D",
  crystal = "Crystal",
  haskell = "Haskell",
  purescript = "PureScript",

  -- Web
  javascript = "JavaScript",
  typescript = "TypeScript",
  typescriptreact = "TSX",
  javascriptreact = "JSX",
  vue = "Vue",
  svelte = "Svelte",
  astro = "Astro",
  css = "CSS",
  sass = "Sass",
  less = "Less",

  -- Data / config
  json = "JSON",
  jsonc = "JSON",
  yaml = "YAML",
  toml = "TOML",
  graphql = "GraphQL",

  -- Markup
  markdown = "Markdown",

  -- Build
  cmake = "CMake",

  -- Other
  gdscript = "GDScript",
}

local descriptive = {
  -- Shell scripts
  sh = "a Shell script (sh)",
  bash = "a Shell script (Bash)",
  zsh = "a Shell script (Zsh)",
  fish = "a Shell script (Fish)",
  csh = "a Shell script (csh)",
  tcsh = "a Shell script (tcsh)",
  nu = "a Shell script (Nushell)",

  -- "an" article (vowel sounds: a, e, f, h, i, m, n, o, r, s, x)
  ada = "an Ada file",
  elixir = "an Elixir file",
  erlang = "an Erlang file",
  fsharp = "an F# file",
  html = "an HTML file",
  ocaml = "an OCaml file",
  objc = "an Objective-C file",
  objcpp = "an Objective-C++ file",
  r = "an R file",
  scss = "an SCSS file",
  sql = "an SQL file",
  xml = "an XML file",

  -- Assembly
  asm = "an Assembly file",
  nasm = "an Assembly file (NASM)",
  masm = "an Assembly file (MASM)",
  fasm = "an Assembly file (FASM)",

  -- Shaders
  glsl = "a GLSL shader",
  hlsl = "an HLSL shader",
  wgsl = "a WGSL shader",

  -- Documents / markup
  tex = "a LaTeX document",
  plaintex = "a LaTeX document",
  rst = "a reStructuredText document",
  typst = "a Typst document",

  -- Config files
  dosini = "an INI config file",
  hcl = "an HCL config file",
  conf = "a config file",

  -- DevOps / infra
  dockerfile = "a Dockerfile",
  terraform = "a Terraform config file",
  proto = "a Protobuf file",

  -- Build systems
  make = "a Makefile",

  -- Vim
  vim = "a Vim script",
  vimdoc = "a Vim help doc",
  help = "a help document",

  -- Git
  gitcommit = "a Git commit message",
  gitrebase = "a Git rebase",
  diff = "a diff",
}

local function format_filetype(opts, action)
  local ft = opts.filetype
  -- Ignore empty, nil, or cord-internal sentinel values like "Cord.unknown"
  if not ft or ft == "" or ft:match("^Cord%.") then
    return action .. " a file..."
  end

  if descriptive[ft] then
    return action .. " " .. descriptive[ft] .. "..."
  end

  local name = pretty[ft] or ft
  local article = name:match("^[AEIOUaeiou]") and "an" or "a"
  return action .. " " .. article .. " " .. name .. " file..."
end

return {
  "vyfor/cord.nvim",
  opts = {
    display = { theme = "atom", flavor = "accent" },
    editor = { tooltip = "Neovim" },

    text = {
      editing = function(opts)
        return format_filetype(opts, "Editing")
      end,
      viewing = function(opts)
        return format_filetype(opts, "Viewing")
      end,
      default = "Doing something...",
      workspace = "",
    },
    buttons = {},
  },
}
