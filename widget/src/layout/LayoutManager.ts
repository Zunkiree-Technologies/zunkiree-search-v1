import { ZK_LAYOUT_CSS } from './zk-layout.css'

const LAYOUT_ROOT_ID = 'zk-layout-root'
const HOST_CONTENT_ID = 'zk-host-content'
const DOCK_PANEL_ID = 'zk-dock-panel'
const STYLE_ID = 'zk-layout-style'

let bootstrapped = false

/**
 * One-time bootstrap: wraps all body children in a flex container.
 * After this call, the DOM structure is:
 *   <body>
 *     <div id="zk-layout-root">          ← flex row
 *       <div id="zk-host-content">       ← flex:1, holds original body children
 *         ...original children...
 *       </div>
 *       <div id="zk-dock-panel" />        ← flex sibling, width toggled via CSS class
 *     </div>
 *   </body>
 *
 * No further DOM mutations happen — dock toggling is CSS-class-only.
 */
export function bootstrap(): void {
  if (bootstrapped) return
  bootstrapped = true

  // Inject layout CSS
  const style = document.createElement('style')
  style.id = STYLE_ID
  style.textContent = ZK_LAYOUT_CSS
  document.head.appendChild(style)

  // Create layout root (flex container)
  const layoutRoot = document.createElement('div')
  layoutRoot.id = LAYOUT_ROOT_ID

  // Create host content wrapper
  const hostContent = document.createElement('div')
  hostContent.id = HOST_CONTENT_ID

  // Create dock panel (empty portal target)
  const dockPanel = document.createElement('div')
  dockPanel.id = DOCK_PANEL_ID

  // Move all existing body children into host content
  while (document.body.firstChild) {
    hostContent.appendChild(document.body.firstChild)
  }

  // Assemble and append
  layoutRoot.appendChild(hostContent)
  layoutRoot.appendChild(dockPanel)
  document.body.appendChild(layoutRoot)
}

/**
 * Full teardown: restores body to its original state.
 */
export function destroy(): void {
  if (!bootstrapped) return

  const layoutRoot = document.getElementById(LAYOUT_ROOT_ID)
  const hostContent = document.getElementById(HOST_CONTENT_ID)
  const style = document.getElementById(STYLE_ID)

  // Move children back to body
  if (hostContent && layoutRoot) {
    while (hostContent.firstChild) {
      document.body.appendChild(hostContent.firstChild)
    }
    layoutRoot.remove()
  }

  style?.remove()
  bootstrapped = false
}

/**
 * Returns the dock panel element for use as a React portal target.
 */
export function getDockPanel(): HTMLElement | null {
  return document.getElementById(DOCK_PANEL_ID)
}
