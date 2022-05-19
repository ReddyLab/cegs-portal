
// Implement insert and range search in an AVL tree https://en.wikipedia.org/wiki/AVL_tree
function RangeTreeNode(data) {
    if (!data) {
        throw "Node must contain data";
    }

    if (data.key === undefined || data.key === null) {
        throw "Data doesn't have a key";
    } else {
        this.key = data.key;
    }
    this.data = data;

    this.balanceFactor = 0;
    this.left = null;
    this.right = null;

    this.link = function(a) {
        if (a == 1) {
            return this.right;
        } else if (a == -1) {
            return this.left;
        } else {
            throw `Invalid link value ${a}`
        }
    }

    this.setLink = function(a, value) {
        if (a == 1) {
            this.right = value;
        } else if (a == -1) {
            this.left = value;
        } else {
            throw `Invalid link value ${a}`
        }
    }

    this._calcBalanceFactors = function(node) {
        if (!node) {
            return 0;
        }

        let rightHeight = this._calcBalanceFactors(node.right);
        let leftHeight = this._calcBalanceFactors(node.left);
        node.balanceFactor = rightHeight - leftHeight;

        return 1 + max(rightHeight, leftHeight);
    }

    this.isLeaf = function() {
        return this.left === null && this.right === null;
    }
}

function RangeTree() {
    this.height = 0;
    this.root;


    // Based on Knuth's AoCP Vol. 3 §6.2.3
    this.insert = function(data) {
        if (data.key === undefined || data.key === null) {
            throw "Data doesn't have a key";
        }
        let key = data.key;

        if (this.root === undefined) {
            this.root = new RangeTreeNode(data);
            return;
        }

        // A1
        let rebalancePointParent = this;
        let rebalancePoint = this.root;
        let p = this.root;
        let pNext;

        while (true) {
            // A2
            if (key < p.key) {
                // A3
                pNext = p.left;
                if (pNext === null) {
                    pNext = new RangeTreeNode(data); // A5
                    p.left = pNext;
                    break;
                } else {
                    if (pNext.balanceFactor != 0) {
                        rebalancePointParent = p;
                        rebalancePoint = pNext;
                    }
                    p = pNext;
                }
            } else if (key > p.key) {
                // A4
                pNext = p.right;
                if (pNext === null) {
                    pNext = new RangeTreeNode(data); // A5
                    p.right = pNext;
                    break;
                } else {
                    if (pNext.balanceFactor != 0) {
                        rebalancePointParent = p;
                        rebalancePoint = pNext;
                    }
                    p = pNext;
                }
            } else {
                break;
                // A5, kinda
                // if (p.isLeaf()) {
                //     console.log("Update leaf")
                //     // Update leaf
                //     return;
                //     pNext = p;
                // } else {
                //     // Go left to find the leaf
                //     let pNext = p.left;
                //     if (pNext.balanceFactor != 0) {
                //         rebalancePointParent = p;
                //         rebalancePoint = pNext;
                //     }
                //     p = pNext;
                // }
            }
        }

        // A6
        let a = 1;
        if (key < rebalancePoint.key) {
            a = -1;
        }
        p = rebalancePoint.link(a);
        let r = p;

        while (p != pNext) {
            if(key < p.key) {
                p.balanceFactor = -1;
                p = p.left;
            } else if (key > p.key) {
                p.balanceFactor = 1;
                p = p.right;
            }
            // } else {
            //     p = p.left;
            // }
        }

        // A7
        if (rebalancePoint.balanceFactor == 0) {
            // The tree grew higher
            rebalancePoint.balanceFactor = a;
            this.height++;
            return;
        } else if (rebalancePoint.balanceFactor == -a) {
            // The tree got more balanced
            rebalancePoint.balanceFactor = 0;
            return;
        } else if (rebalancePoint.balanceFactor == a) {
            if (r.balanceFactor == a) {
                // A8
                // Single rotation
                p = r;
                rebalancePoint.setLink(a, r.link(-a));
                r.setLink(-a, rebalancePoint);
                rebalancePoint.balanceFactor = 0;
                r.balanceFactor = 0;
            } else if (r.balanceFactor == -a) {
                // A9
                // Double rotation
                p = r.link(-a);
                r.setLink(-a, p.link(a));
                p.setLink(a, r);
                rebalancePoint.setLink(a, p.link(-a));
                p.setLink(-a, rebalancePoint);
                if (p.balanceFactor == a){
                    rebalancePoint.balanceFactor = -a;
                    r.balanceFactor = 0;
                } else if (p.balanceFactor == 0) {
                    rebalancePoint.balanceFactor = 0;
                    r.balanceFactor = 0;
                } else if (p.balanceFactor == -a) {
                    rebalancePoint.balanceFactor = 0;
                    r.balanceFactor = a;
                }
                p.balanceFactor = 0;
            }
        }

        // A10
        if (rebalancePointParent === this){
            this.root = p;
        } else if (rebalancePoint === rebalancePointParent.right) {
            rebalancePointParent.right = p;
        } else {
            rebalancePointParent.left = p;
        }
    };

    this.count = function() {
        let count = 0;

        let toCheck = [this.root];
        while (toCheck.length != 0) {
            let node = toCheck.shift();
            if (node.isLeaf()) {
                count += 1;
            } else {
                count += 1;
                if (node.left) {
                    toCheck.push(node.left);
                }
                if (node.right) {
                    toCheck.push(node.right);
                }
            }
        }

        return count;
    }

    this.print = function() {
        let nextLevel = [];
        let toPrint = [this.root];
        let fullString = "";
        while (toPrint.length != 0) {
            let levelString = "";
            while(toPrint.length != 0) {
                let node = toPrint.shift();
                if (node) {
                    levelString += `${node.key}(${node.balanceFactor}) `;
                    nextLevel.push(node.left);
                    nextLevel.push(node.right);
                } else {
                    levelString += ` .   `;
                }
            }
            fullString += levelString + "\n";
            toPrint = nextLevel;
            nextLevel = [];
        }
        console.log(fullString);
    }

    this.search = function(x, y) {
        let vSplit = this._findSplitNode(x, y);
        let values = []
        if (vSplit.isLeaf()) {
            let vSplitKey = vSplit.data.key;
            if (vSplitKey >= x || vSplitKey < y) {
                values.push(vSplit.data)
            }
        } else {
            let node = vSplit.left;
            while (!node.isLeaf()) {
                let nodeKey = node.data.key
                if (x <= nodeKey) {
                    values.push(...this._subtreeLeafData(node.right))
                    node = node.left;
                } else {
                    node = node.right;
                }
            }
            let nodeKey = node.data.key;
            if (nodeKey >= x && nodeKey <= y) {
                values.unshift(node.data)
            }
            node = vSplit.right;
            while (!node.isLeaf()) {
                let nodeKey = node.data.key
                if (y >= nodeKey) {
                    values.push(...this._subtreeLeafData(node.left))
                    node = node.right;
                } else {
                    node = node.left;
                }
            }
            nodeKey = node.data.key;
            if (nodeKey >= x && nodeKey <= y) {
                values.push(node.data)
            }
        }

        return values;
    }

    this._findSplitNode = function(x, y) {
        let node = this;
        let nodeKey = node.data.key;
        while (!node.isLeaf() && (x > nodeKey || y <= nodeKey)) {
            if (y <= nodeKey) {
                node = node.left;
            } else {
                node = node.right;
            }
            nodeKey = node.key;
        }
        return node;
    }

    this._subtreeLeafData = function(node) {
        if (!node) {
            return [];
        }

        let leaves = [];
        let toCheck = [node];

        while (toCheck.length != 0) {
            let check = toCheck.shift();
            if (check.isLeaf()) {
                leaves.push(check.data);
            } else {
                if (check.left) {
                    toCheck.unshift(check.left);
                }
                if (check.right) {
                    toCheck.unshift(check.right);
                }
            }
        }
    }
}

module.exports = { RangeTree, RangeTreeNode }
