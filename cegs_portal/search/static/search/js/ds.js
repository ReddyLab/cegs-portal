
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


    // AVL insert based on Knuth's AoCP Vol. 3 §6.2.3
    this.insert = function(data) {
        if (data.key === undefined || data.key === null) {
            throw "Data doesn't have a key";
        }
        let key = data.key;

        if (this.root === undefined) {
            this.root = new RangeTreeNode(data);
            return;
        }

        // A1: Initialize
        let rebalancePointParent = this;
        let rebalancePoint = this.root;
        let p = this.root;
        let pNext;

        // A2: Compare key values
        while (true) {
            if (key < p.key) {
                // A3: Move left
                pNext = p.left;
                if (pNext === null) {
                    // Inserts are always at leaves
                    pNext = new RangeTreeNode(data); // A5: Insert
                    let newNode = new RangeTreeNode(p.data)
                    p.left = pNext;
                    p.right = newNode;
                    p.key = data.key;
                    p.data = data;
                    p.balanceFactor = 0;
                    break;
                } else {
                    if (pNext.balanceFactor != 0) {
                        rebalancePointParent = p;
                        rebalancePoint = pNext;
                    }
                    p = pNext;
                }
            } else if (key > p.key) {
                // A4: Move right
                pNext = p.right;
                if (pNext === null) {
                    // Inserts are always at leaves
                    pNext = new RangeTreeNode(data); // A5: Insert
                    let newNode = new RangeTreeNode(p.data)
                    p.right = pNext;
                    p.left = newNode;
                    break;
                } else {
                    if (pNext.balanceFactor != 0) {
                        rebalancePointParent = p;
                        rebalancePoint = pNext;
                    }
                    p = pNext;
                }
            } else {
                // A5: Insert, kinda
                if (p.isLeaf()) {
                    // Update leaf, terminate algorithm
                    return;
                } else {
                    pNext = p.left;
                    // Go left to find the leaf
                    if (pNext.balanceFactor != 0) {
                        rebalancePointParent = p;
                        rebalancePoint = pNext;
                    }
                    p = pNext;
                }
            }
        }

        // rebalancePoint is either root or the lowest unbalanced node along the insertion path
        // p = parent of the new node

        // A6: Adjust balance factors

        if (p === rebalancePoint) {
            // No rebalancing needed
            return;
        }
        // 'a' is the "kind" of unbalancing that happened.
        // -1 -- left-unbalanced
        // +1 -- right-unbalanced
        let a = key < rebalancePoint.key ? -1 : 1;
        p = rebalancePoint.link(a);
        let r = p;

        // p, r are the potentially unbalancing child of rebalancePoint
        // pNext is the newly inserted node

        // Every point between p and pNext is marked as balanced. Now that a new node (raelly two) has been added
        // that shouldn't be true anymore, except for pNext's parent. pNext's parent should now have two children,
        // pNext and a copy of itself, so it is balanced.
        while (p.left != pNext && p.right != pNext) {
            if(key < p.key) {
                p.balanceFactor = -1;
                p = p.left;
            } else if (key > p.key) {
                p.balanceFactor = 1;
                p = p.right;
            } else {
                p = p.left;
            }
        }

        // A7: Balancing act (rotate the nodes)
        if (rebalancePoint.balanceFactor == 0) {
            // The tree was balanced, so it just grew 1 higher. No need to rotate anything.
            rebalancePoint.balanceFactor = a;
            this.height++;
            return;
        } else if (rebalancePoint.balanceFactor == -a) {
            // The tree was imbalanced to side "-a". The new node was added to side "a", so
            // the tree got more balanced. No need to rotate anything.
            rebalancePoint.balanceFactor = 0;
            return;
        } else if (rebalancePoint.balanceFactor == a) {
            // The tree was already imbalanced to side "a" and then the new node was added also to side "a".
            // The tree is definitely imbalanced, so a rotation is needed.
            // 'r' is the child of rebalancePoint the new node is under.
            if (r.balanceFactor == a) {
                // A8
                // Single rotation
                // The new node is on the same side of 'r' as 'r' is of rebalancePoint, corresponding to Case I
                // in AoCP
                p = r;
                rebalancePoint.setLink(a, r.link(-a));
                r.setLink(-a, rebalancePoint);
                rebalancePoint.balanceFactor = 0;
                r.balanceFactor = 0;
            } else if (r.balanceFactor == -a) {
                // A9
                // Double rotation
                // The new node is on the side of 'r' different than the side 'r' is of rebalancePoint,
                // corresponding to Case II in AoCP
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

        // A10: Finishing touch
        // Change rotation point parent to point at the new root of the rotated subtree
        if (rebalancePointParent === this){
            // Handle the case where the rotation point parent is the root of the tree
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
                    levelString += `${node.key}(${node.balanceFactor})${node.isLeaf() ? '*' : ''} `;
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
            let vSplitKey = vSplit.key;
            if (vSplitKey >= x || vSplitKey <= y) {
                values.push(vSplit.data)
            }
        } else {
            let node = vSplit.left;
            while (!node.isLeaf()) {
                if (x <= node.key) {
                    values.unshift(...this._subtreeLeafData(node.right))
                    node = node.left;
                } else {
                    node = node.right;
                }
            }
            if (node.key >= x && node.key <= y) {
                values.unshift(node.data)
            }
            node = vSplit.right;
            while (!node.isLeaf()) {
                if (y >= node.key) {
                    values.push(...this._subtreeLeafData(node.left))
                    node = node.right;
                } else {
                    node = node.left;
                }
            }
            if (node.key >= x && node.key <= y) {
                values.push(node.data)
            }
        }

        return values;
    }

    this._findSplitNode = function(x, y) {
        let node = this.root;
        let nodeKey = node.key;
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
                if (check.right) {
                    toCheck.unshift(check.right);
                }
                if (check.left) {
                    toCheck.unshift(check.left);
                }
            }
        }

        return leaves;
    }
}

module.exports = { RangeTree, RangeTreeNode }
