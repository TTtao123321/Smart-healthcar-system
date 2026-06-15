<template>
    <div v-if="isAuth(['ROOT', 'ROLE:SELECT'])">
        <el-form :inline="true">
            <el-form-item>
                <el-button type="primary" :disabled="!isAuth(['ROOT', 'ROLE:INSERT'])" @click="addHandle()">新增</el-button>
            </el-form-item>
        </el-form>
        <el-table :data="dataList" border v-loading="dataListLoading" :cell-style="{ padding: '3px 0' }" style="width: 100%;">
            <el-table-column type="index" header-align="center" align="center" width="100" label="序号">
                <template #default="scope">
                    <span>{{ scope.$index + 1 }}</span>
                </template>
            </el-table-column>
            <el-table-column prop="roleName" header-align="center" align="center" min-width="150" label="角色名称" />
            <el-table-column prop="desc" header-align="center" align="center" min-width="200" label="描述" :show-overflow-tooltip="true" />
            <el-table-column header-align="center" align="center" min-width="100" label="系统内置">
                <template #default="scope">
                    <el-tag :type="scope.row.systemic ? 'danger' : 'success'">{{ scope.row.systemic ? '是' : '否' }}</el-tag>
                </template>
            </el-table-column>
            <el-table-column header-align="center" align="center" min-width="120" label="权限数量">
                <template #default="scope">
                    <span>{{ scope.row.permissions ? scope.row.permissions.length : 0 }}个</span>
                </template>
            </el-table-column>
            <el-table-column header-align="center" align="center" width="150" label="操作">
                <template #default="scope">
                    <el-button type="text" :disabled="!isAuth(['ROOT', 'ROLE:UPDATE'])" @click="updateHandle(scope.row)">修改</el-button>
                    <el-button type="text" :disabled="!isAuth(['ROOT', 'ROLE:DELETE']) || scope.row.systemic" @click="deleteHandle(scope.row.id)">删除</el-button>
                </template>
            </el-table-column>
        </el-table>

        <el-dialog :title="dialogTitle" v-model="dialogVisible" width="500px" :close-on-click-modal="false">
            <el-form :model="dataForm" :rules="dataRule" ref="dataForm" label-width="80px">
                <el-form-item label="角色名称" prop="roleName">
                    <el-input v-model="dataForm.roleName" placeholder="角色名称" />
                </el-form-item>
                <el-form-item label="描述" prop="desc">
                    <el-input v-model="dataForm.desc" placeholder="描述" type="textarea" :rows="3" />
                </el-form-item>
                <el-form-item label="权限" prop="permissions">
                    <el-tree
                        ref="permissionTree"
                        :data="permissionTreeData"
                        :props="treeProps"
                        node-key="id"
                        show-checkbox
                        :default-checked-keys="dataForm.permissions"
                        :check-strictly="false"
                    />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="dialogVisible = false">取消</el-button>
                <el-button type="primary" @click="submitHandle()">确定</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script>
export default {
    data: function() {
        return {
            dataList: [],
            dataListLoading: false,
            dialogVisible: false,
            dialogTitle: '',
            dataForm: {
                id: null,
                roleName: '',
                desc: '',
                permissions: []
            },
            dataRule: {
                roleName: [{ required: true, message: '角色名称不能为空', trigger: 'blur' }]
            },
            permissionList: [],
            permissionTreeData: [],
            treeProps: {
                children: 'children',
                label: 'label'
            }
        };
    },
    methods: {
        loadDataList: function() {
            let that = this;
            that.dataListLoading = true;
            that.$http('role/selectAllRoles', 'GET', null, true, function(resp) {
                that.dataList = resp.result;
                that.dataListLoading = false;
            });
        },
        loadPermissionList: function() {
            let that = this;
            that.$http('permission/selectAllPermissions', 'GET', null, true, function(resp) {
                that.permissionList = resp.result;
                that.buildPermissionTree();
            });
        },
        buildPermissionTree: function() {
            let that = this;
            let map = {};
            let tree = [];
            for (let one of that.permissionList) {
                let moduleName = one.moduleName;
                if (!map[moduleName]) {
                    map[moduleName] = {
                        id: 'module_' + moduleName,
                        label: moduleName,
                        children: []
                    };
                    tree.push(map[moduleName]);
                }
                map[moduleName].children.push({
                    id: one.id,
                    label: one.permissionName,
                    permissionName: one.permissionName,
                    moduleName: one.moduleName,
                    actionName: one.actionName
                });
            }
            that.permissionTreeData = tree;
        },
        addHandle: function() {
            let that = this;
            that.dialogTitle = '新增角色';
            that.dataForm = {
                id: null,
                roleName: '',
                desc: '',
                permissions: []
            };
            that.dialogVisible = true;
            that.$nextTick(() => {
                if (that.$refs.permissionTree) {
                    that.$refs.permissionTree.setCheckedKeys([]);
                }
            });
        },
        updateHandle: function(row) {
            let that = this;
            that.dialogTitle = '修改角色';
            that.dataForm = {
                id: row.id,
                roleName: row.roleName,
                desc: row.desc,
                permissions: row.permissions ? row.permissions.map(p => p.id) : []
            };
            that.dialogVisible = true;
            that.$nextTick(() => {
                if (that.$refs.permissionTree) {
                    that.$refs.permissionTree.setCheckedKeys(that.dataForm.permissions);
                }
            });
        },
        submitHandle: function() {
            let that = this;
            that.$refs['dataForm'].validate(valid => {
                if (valid) {
                    let checkedNodes = that.$refs.permissionTree.getCheckedNodes(false, true);
                    let permissionIds = checkedNodes.filter(n => !String(n.id).startsWith('module_')).map(n => n.id);
                    let data = {
                        id: that.dataForm.id,
                        roleName: that.dataForm.roleName,
                        desc: that.dataForm.desc,
                        permissionIds: permissionIds
                    };
                    let url = that.dataForm.id ? 'role/updateRole' : 'role/insertRole';
                    that.$http(url, 'POST', data, true, function(resp) {
                        ElMessage({
                            message: '操作成功',
                            type: 'success',
                            duration: 1200,
                            onClose: () => {
                                that.dialogVisible = false;
                                that.loadDataList();
                            }
                        });
                    });
                } else {
                    return false;
                }
            });
        },
        deleteHandle: function(id) {
            let that = this;
            ElMessageBox.confirm('确定要删除该角色？', '提示信息', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(() => {
                that.$http('role/deleteRoleById?id=' + id, 'POST', null, true, function(resp) {
                    ElMessage({
                        message: '操作成功',
                        type: 'success',
                        duration: 1200,
                        onClose: () => {
                            that.loadDataList();
                        }
                    });
                });
            });
        }
    },
    created: function() {
        this.loadDataList();
        this.loadPermissionList();
    }
};
</script>

<style></style>
VUEEOF; __tr_native_ec=$?; pwd -P >| '/var/folders/hn/1ylcxx294sz85pbtym3z3h880000gn/T/agent-toolhost/jobs/job-98ffba35540d45fea584ce2e165ed747/cwd.txt'; exit "$__tr_native_ec"