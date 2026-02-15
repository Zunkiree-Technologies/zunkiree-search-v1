/**
 * Layout CSS for the dock architecture.
 * Injected once at bootstrap, removed on destroy.
 */
export const ZK_LAYOUT_CSS = `
  #zk-layout-root {
    display: flex;
    width: 100%;
    min-height: 100vh;
  }

  #zk-host-content {
    flex: 1;
    min-width: 0;
  }

  #zk-dock-panel {
    position: sticky;
    top: 0;
    height: 100vh;
    align-self: flex-start;
    width: 0;
    flex-shrink: 0;
    overflow: hidden;
  }

  #zk-layout-root.zk-dock-active #zk-dock-panel {
    width: 420px;
    border-left: 1px solid rgba(0, 0, 0, 0.06);
    transition: width 200ms ease;
  }
`
