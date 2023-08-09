import { RangeTree, RangeTreeNode } from './ds.mjs';

test("Create new RangeTreeNode", () => {
    expect(new RangeTreeNode({key: 1})).toBeTruthy();
});

test("Create a new RangeTreeNode without data", () => {
    expect(() => new RangeTreeNode()).toThrow("Node must contain data");
});

test("Create a new RangeTreeNode without a key", () => {
    expect(() => new RangeTreeNode({data: 1})).toThrow("Data doesn't have a key");
});

test("Check RangeTreeNode links", () => {
    let root = new RangeTreeNode({key: 1});
    root.left = new RangeTreeNode({key: 2});
    root.right = new RangeTreeNode({key: 3});
    expect(root.link(1).key).toEqual(3);
    expect(root.link(-1).key).toEqual(2);
    expect(() => root.link(3).key).toThrow("Invalid link value 3");
});

test("Check RangeTreeNode links", () => {
    let root = new RangeTreeNode({key: 1});
    let left = new RangeTreeNode({key: 2});
    let right = new RangeTreeNode({key: 3});
    root.setLink(1, right);
    root.setLink(-1, left)
    expect(root.right.key).toEqual(3);
    expect(root.left.key).toEqual(2);
    expect(() => root.setLink(3, left)).toThrow("Invalid link value 3");
});

test("Check RangeTreeNode is Leaf", () => {
    let root = new RangeTreeNode({key: 1});

    expect(root.isLeaf()).toBeTruthy();

    root.left = new RangeTreeNode({key: 2});

    expect(root.isLeaf()).toBeFalsy();
});

test("create new RangeTree", () => {
    expect(new RangeTree()).toBeTruthy();
});

test("Insert an object without a key", () => {
    let tree = new RangeTree();
    expect(() => tree.insert({foo: 1})).toThrow("Data doesn't have a key");
});

test("Insert an object", () => {
    let tree = new RangeTree();
    tree.insert({key: 1});
    expect(tree.count()).toEqual(1);
});

test("Insert several objects", () => {
    let tree = new RangeTree();
    for (let k of [6, 7, 9, 3, 2, 1, 0, 4, 8, 5]) {
        tree.insert({key: k});
    }
    expect(tree.count()).toEqual(19);
    expect(tree.root.key).toEqual(2);

    tree = new RangeTree();
    for (let k of [6, 13, 12, 17, 19, 7, 15, 0, 8, 5, 9, 11, 1, 10, 18, 16, 4, 2, 3, 14]) {
        tree.insert({key: k});
    }
    expect(tree.count()).toEqual(39);
    expect(tree.root.key).toEqual(8);

    tree = new RangeTree();
    for (let k of [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]) {
        tree.insert({key: k});
    }
    expect(tree.count()).toEqual(39);
    expect(tree.root.key).toEqual(7);

    tree = new RangeTree();
    for (let k of [19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]) {
        tree.insert({key: k});
    }
    expect(tree.count()).toEqual(39);
    expect(tree.root.key).toEqual(11);
});

let bigTree;
test("Insert lots of objects", () => {
    bigTree = new RangeTree();
    for (let k = 0; k < 1000000; k++) {
        bigTree.insert({key: k});
    }
    expect(bigTree.count()).toEqual(1999999);
    expect(bigTree.root.key).toEqual(524287);
});

test("Search for items in range", () => {
    let tree = new RangeTree();
    for (let k of [6, 13, 12, 17, 19, 7, 15, 0, 8, 5, 9, 11, 1, 10, 18, 16, 4, 2, 3, 14]) {
        tree.insert({key: k});
    }
    expect(tree.search(1.5, 7.5).map(n => n.key)).toEqual([2, 3, 4, 5, 6, 7]);
    expect(tree.search(11.5, 17.5).map(n => n.key)).toEqual([12, 13, 14, 15, 16, 17]);
    expect(tree.search(1.5, 17.5).map(n => n.key)).toEqual([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]);
    expect(tree.search(-5, 5).map(n => n.key)).toEqual([0, 1, 2, 3, 4, 5]);
    expect(tree.search(15, 25).map(n => n.key)).toEqual([15, 16, 17, 18, 19]);
})

let bigTreeSearchResult = []
for (let r = 100001; r <= 200007; r++) {
    bigTreeSearchResult.push(r);
}

test("Search lots of objects", () => {
    expect(bigTree.search(100000.5, 200007.5).map(n => n.key)).toEqual(bigTreeSearchResult);
});
