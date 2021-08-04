const assert = require('chai').assert
const fizzbuzz = require('../fizzbuzz')

describe('Fizzbuzz', function() {
    it('returns 1 with 1 passed in', function() {
        fizzbuzz(1,'1')
    })
    it('returns 2 with 2 passed in', function() {
        fizzbuzz(2,'2')
    })
})