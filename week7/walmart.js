let item = []
let price = []
let tot = 0
function addItem(t) {
    item.push(t)
}
function addPrice(p) {
    price.push(p)
}
function total() {
    for (i=0; i< price.length; i++) {
        tot +=price[i]
    }
    console.log(tot)
}
function discount() {
    for (i=0; i< price.length; i++) {
        tot +=price[i]
    }
    console.log(tot - (tot * 60/100))
}
addItem('milk')
addItem('bread')
console.log(item)
addPrice(5)
addPrice(5)
console.log(price)
total()
discount()