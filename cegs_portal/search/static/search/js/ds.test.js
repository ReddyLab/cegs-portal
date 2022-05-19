const { RangeTree, RangeTreeNode } = require('./ds');

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
    let keys = [6, 7, 9, 3, 2, 1, 0, 4, 8, 5];
    for (k of keys) {
        tree.insert({key: k});
    }
    expect(tree.count()).toEqual(10);
    expect(tree.root.key).toEqual(3);
});
