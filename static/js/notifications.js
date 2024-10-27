
// notifications.js
class Notifications {
    constructor(el) {
      this.el = el
    }
    
    createDiv(className = "") {
      const el = document.createElement("div")
      el.classList.add(className)
      return el
    }
  
    addText(el, text) {
      el.appendChild(document.createTextNode(text))
    }
    
    create(
      title = "Untitled notification",
      description = "",
      duration = 2,
      destroyOnClick = false,
      clickFunction = undefined
    ) {
      
      function destroy(animate) {
        if (animate) {
          notiEl.classList.add("out")
          notiEl.addEventListener("animationend", () => {notiEl.remove()})
        } else {
          notiEl.remove()
        }
      }
      
      const notiEl = this.createDiv("noti")
      const notiCardEl = this.createDiv("noticard")
      const glowEl = this.createDiv("notiglow")
      const borderEl = this.createDiv("notiborderglow")
      
      const titleEl = this.createDiv("notititle")
      this.addText(titleEl, title)
      
      const descriptionEl = this.createDiv("notidesc")
      this.addText(descriptionEl, description)
      
      notiEl.appendChild(notiCardEl)
      notiCardEl.appendChild(glowEl)
      notiCardEl.appendChild(borderEl)
      notiCardEl.appendChild(titleEl)
      notiCardEl.appendChild(descriptionEl)
      
      this.el.appendChild(notiEl)
      
  
      requestAnimationFrame(function() {
        notiEl.style.height = "calc(0.25rem + " + notiCardEl.getBoundingClientRect().height + "px)";
      });
  
  
      notiEl.addEventListener("mousemove", (event) => {
        const rect = notiCardEl.getBoundingClientRect()
        const localX = (event.clientX - rect.left) / rect.width
        const localY = (event.clientY - rect.top) / rect.height
  
        glowEl.style.left = localX * 100 + "%"
        glowEl.style.top = localY * 100 + "%"
  
        borderEl.style.left = localX * 100 + "%"
        borderEl.style.top = localY * 100 + "%"
      });
      
      if (clickFunction != undefined) {
        notiEl.addEventListener("click", clickFunction)
      }
      
  
      if (destroyOnClick) {
        notiEl.addEventListener("click", () => destroy(true))
      }
      
      if (duration != 0) {
        setTimeout(() => {
          notiEl.classList.add("out")
          notiEl.addEventListener("animationend", () => {notiEl.remove()})
        }, duration * 1000)
      }
      return notiEl
    }
  }