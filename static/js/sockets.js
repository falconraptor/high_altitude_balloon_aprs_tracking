class Socket {
    constructor (url, message, open, close, connect=true) {
        this.url = url
        this.ws = window['MozWebSocket'] ? MozWebSocket : WebSocket
        this.message = (message) ? (Array.isArray(message)) ? message : [message] : []
        this.open = (open) ? (Array.isArray(open)) ? open : [open] : []
        this.close = (close) ? (Array.isArray(close)) ? close : [close] : []
        if (connect) this.connect_socket()
        return this
    }
    connect_socket(message, open, close) {
        this.webSocket = new this.ws(this.url)
        if (message != null) this.message.push(message)
        this.webSocket.onmessage = event => this.message.forEach(elem => {
            if (typeof elem != 'undefined') elem(event)
        })
        if (open != null) this.open.push(open)
        this.webSocket.onopen = event => this.open.forEach(elem => {
            if (typeof elem != 'undefined') elem(event)
        })
        this.webSocket.onclose = (event) => {
            setTimeout(() => {
                try {
                    this.connect_socket()
                } catch (e) {
                    this.close_socket()
                }
            }, Number((Math.random() * 3000 + 1000).toFixed(0)))
            this.close.forEach(elem => {
                if (typeof elem != 'undefined') elem(event)
            })
        }
        if (close != null) this.close.push(close)
        return this
    }
    close_socket() {
        try {
            this.webSocket.close()
        } catch (e) {}
        return this
    }
    send(msg) {
        this.webSocket.send(msg)
        return this
    }
    json(obj) {
        this.webSocket.send(JSON.stringify(obj))
        return this
    }
}
