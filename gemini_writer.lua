local layout = pandoc.layout
local space = layout.space
local blankline = layout.blankline
local cr = layout.cr
local hang = layout.hang
local concat = layout.concat
local nowrap = layout.nowrap

local table_gen = require('table_gen')

local TAB_SIZE = 2

Writer = pandoc.scaffolding.Writer

Writer.Block.Plain = function(el)
  return {Writer.Inlines(el.content)}
end

Writer.Inline.Str = function(str)
  return str.text
end

Writer.Inline.Emph = function(el)
  return concat { '*', Writer.Inlines(el.content), '*' }
end

Writer.Inline.Strong = function(el)
  return concat { '**', Writer.Inlines(el.content), '**' }
end

Writer.Inline.Span = function(el)
  return { Writer.Inlines(el.content) }
end

Writer.Inline.LineBreak = cr

Writer.Inline.SoftBreak = function(br, opts)
  return space
end

Writer.Inline.Code = function(el)
  return el.text
end

Writer.Inline.Space = space
local pending_links = {}

function clear_pending_links()
  for i, v in ipairs(pending_links) do
    pending_links[i] = nil
  end
end

function has_class(className, elem)
  for i, kls in ipairs(elem.attr.classes) do
    if kls == className then
      return true
    end
  end
  return false
end

Writer.Inline.Link = function(link)
  table.insert(pending_links, {target = link.target, content = link.content })
  if has_class("gem-hidden", link) then
    return {}
  else
    return {Writer.Inlines(link.content)}
  end
end

function dump_pending_links()
  local function render_link(link)
    local target = link.target .. ".gmi"
    target = string.gsub(target, "/%.gmi", ".gmi")
    return concat { '=> ', target, ' ', nowrap(Writer.Inlines(link.content)), cr }
  end
  local content = {}
  for i, link in ipairs(pending_links) do
    table.insert(content, render_link(link))
  end
  clear_pending_links()
  return content
end

Writer.Block.Para = function(para)
  return concat { Writer.Inlines(para.content), blankline, table.unpack(dump_pending_links()) }
end

Writer.Block.BlockQuote = function(bq)
  return concat { Writer.Blocks(bq.content), blankline, table.unpack(dump_pending_links()) }
end

Writer.Block.Header = function(el)
  if el.level == 2 then
    return concat { '# ', Writer.Inlines(el.content) }
  elseif el.level == 3 then
    return concat { '## ', Writer.Inlines(el.content)  }
  elseif el.level > 3 then
    return concat { '### ', Writer.Inlines(el.content) }
  else -- level == 1, title, ignore
    return concat { '# *', Writer.Inlines(el.content), '*' }
  end
end

Writer.Block.Div = function(div)
  return Writer.Blocks(div.content)
end

Writer.Block.BulletList = function(el)
  local function render_item(item)
    return concat { hang(Writer.Blocks(item), TAB_SIZE, "* "), cr }
  end
  local content = el.content:map(render_item)
  table.insert(content, blankline)
  for i, link in ipairs(dump_pending_links()) do
    table.insert(content, link)
  end
  return content
end

Writer.Block.OrderedList = function(el)
  local counter = 0
  local function render_item(item)
    counter = counter + 1
    return concat { hang(Writer.Blocks(item), TAB_SIZE, counter .. "."), cr }
  end
  return concat(el.content:map(render_item))
end

local table_header = {}
local table_rows = {}

Writer.Block.Table = function(tbl)
  print(tbl)
  return { Writer.Blocks(tbl.content) }
end

Writer.Block.Row = function(row)
  print(row)
  return { Writer.Blocks(row.content) }
end

Writer.Block.Cell = function(cell)
  print(cell)
  return { Writer.Blocks(cell.content) }
end
