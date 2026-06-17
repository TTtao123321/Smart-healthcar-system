<template>
    <div v-if="isAuth(['ROOT', 'USER:SELECT'])">
        <el-form :inline="true" :model="searchForm" ref="searchForm">
            <el-form-item>
                <el-input v-model="searchForm.name" placeholder="姓名" class="input" clearable />
            </el-form-item>
            <el-form-item>
                <el-button type="primary" @click="searchHandle()">查询</el-button>
                <el-button type="primary" :disabled="!isAuth(['ROOT', 'USER:INSERT'])" @click="addHandle()">新增</el-button>
                <el-button type="danger" :disabled="!isAuth(['ROOT', 'USER:DELETE'])" @click="deleteHandle()">批量删除</el-button>
            </el-form-item>
        </el-form>
        <el-table :data="dataList" border v-loading="dataListLoading" @selection-change="selectionChangeHandle" :cell-style="{ padding: '3px 0' }" style="width: 100%;">
            <el-table-column type="selection" header-align="center" align="center" width="50" />
            <el-table-column type="index" header-align="center" align="center" width="100" label="序号">
                <template #default="scope">
                    <span>{{ (pageIndex - 1) * pageSize + scope.$index + 1 }}</span>
                </template>
            </el-table-column>
            <el-table-column prop="username" header-align="center" align="center" min-width="120" label="用户名" />
            <el-table-column prop="name" header-align="center" align="center" min-width="100" label="姓名" />
            <el-table-column prop="sex" header-align="center" align="center" min-width="70" label="性别" />
            <el-table-column prop="tel" header-align="center" align="center" min-width="120" label="电话" />
            <el-table-column prop="email" header-align="center" align="center" min-width="180" label="邮箱" :show-overflow-tooltip="true" />
            <el-table-column prop="job" header-align="center" align="center" min-width="100" label="职位" />
            <el-table-column header-align="center" align="center" min-width="150" label="角色" :show-overflow-tooltip="true">
                <template #default="scope">
                    <span>{{ scope.row.roleNames ? scope.row.roleNames.join('、') : '' }}</span>
                </template>
            </el-table-column>
            <el-table-column prop="deptName" header-align="center" align="center" min-width="120" label="科室" />
            <el-table-column header-align="center" align="center" min-width="80" label="状态">
                <template #default="scope">
                    <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'">{{ scope.row.status === 1 ? '正常' : '禁用' }}</el-tag>
                </template>
            </el-table-column>
            <el-table-column header-align="center" align="center" width="150" label="操作">
                <template #default="scope">
                    <el-button type="text" :disabled="!isAuth(['ROOT', 'USER:UPDATE'])" @click="updateHandle(scope.row)">修改</el-button>
                    <el-button type="text" :disabled="!isAuth(['ROOT', 'USER:DELETE'])" @click="deleteHandle(scope.row.id)">删除</el-button>
                </template>
            </el-table-column>
        </el-table>
        <el-pagination
            @size-change="sizeChangeHandle"
            @current-change="currentChangeHandle"
            :current-page="pageIndex"
            :page-sizes="[10, 20, 50]"
            :page-size="pageSize"
            :total="totalCount"
            layout="total, sizes, prev, pager, next, jumper"
        />

        <el-dialog :title="dialogTitle" v-model="dialogVisible" width="500px" :close-on-click-modal="false">
            <el-form :model="dataForm" :rules="dataRule" ref="dataForm" label-width="80px">
                <el-form-item label="用户名" prop="username">
                    <el-input v-model="dataForm.username" placeholder="用户名" />
                </el-form-item>
                <el-form-item label="密码" prop="password" v-if="!dataForm.id">
                    <el-input v-model="dataForm.password" type="password" placeholder="密码" />
                </el-form-item>
                <el-form-item label="姓名" prop="name">
                    <el-input v-model="dataForm.name" placeholder="姓名" />
                </el-form-item>
                <el-form-item label="性别" prop="sex">
                    <el-select v-model="dataForm.sex" placeholder="性别" style="width: 100%;">
                        <el-option label="男" value="男" />
                        <el-option label="女" value="女" />
                    </el-select>
                </el-form-item>
                <el-form-item label="电话" prop="tel">
                    <el-input v-model="dataForm.tel" placeholder="电话" />
                </el-form-item>
                <el-form-item label="邮箱" prop="email">
                    <el-input v-model="dataForm.email" placeholder="邮箱" />
                </el-form-item>
                <el-form-item label="职位" prop="job">
                    <el-input v-model="dataForm.job" placeholder="职位" />
                </el-form-item>
                <el-form-item label="角色" prop="roleIds">
                    <el-select v-model="dataForm.roleIds" multiple placeholder="选择角色" style="width: 100%;">
                        <el-option v-for="one in roleList" :label="one.roleName" :value="one.id" />
                    </el-select>
                </el-form-item>
                <el-form-item label="科室" prop="deptId">
                    <el-select v-model="dataForm.deptId" placeholder="选择科室" style="width: 100%;">
                        <el-option v-for="one in deptList" :label="one.name" :value="one.id" />
                    </el-select>
                </el-form-item>
                <el-form-item label="状态" prop="status">
                    <el-select v-model="dataForm.status" placeholder="状态" style="width: 100%;">
                        <el-option label="正常" :value="1" />
                        <el-option label="禁用" :value="2" />
                    </el-select>
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
            searchForm: {
                name: ''
            },
            dataList: [],
            pageIndex: 1,
            pageSize: 10,
            totalCount: 0,
            dataListLoading: false,
            dataListSelections: [],
            dialogVisible: false,
            dialogTitle: '',
            dataForm: {
                id: null,
                username: '',
                password: '',
                name: '',
                sex: '',
                tel: '',
                email: '',
                job: '',
                roleIds: [],
                deptId: null,
                status: 1
            },
            dataRule: {
                username: [{ required: true, message: '用户名不能为空', trigger: 'blur' }],
                password: [{ required: true, message: '密码不能为空', trigger: 'blur' }],
                name: [{ required: true, message: '姓名不能为空', trigger: 'blur' }]
            },
            roleList: [],
            deptList: []
        };
    },
    methods: {
        loadDataList: function() {
            let that = this;
            that.dataListLoading = true;
            let data = {
                page: that.pageIndex,
                length: that.pageSize,
                name: that.searchForm.name || null
            };
            that.$http('user/selectUserByPage', 'POST', data, true, function(resp) {
                let result = resp.result;
                that.dataList = result.list;
                that.totalCount = result.totalCount;
                that.dataListLoading = false;
            });
        },
        loadRoleList: function() {
            let that = this;
            that.$http('role/selectAllRoles', 'GET', null, true, function(resp) {
                that.roleList = resp.result;
            });
        },
        loadDeptList: function() {
            let that = this;
            that.$http('medical/dept/selectAllDeptNameAndId', 'GET', null, true, function(resp) {
                that.deptList = resp.result;
            });
        },
        sizeChangeHandle: function(val) {
            this.pageSize = val;
            this.pageIndex = 1;
            this.loadDataList();
        },
        currentChangeHandle: function(val) {
            this.pageIndex = val;
            this.loadDataList();
        },
        searchHandle: function() {
            if (this.pageIndex != 1) {
                this.pageIndex = 1;
            }
            this.loadDataList();
        },
        selectionChangeHandle: function(val) {
            this.dataListSelections = val;
        },
        addHandle: function() {
            let that = this;
            that.dialogTitle = '新增用户';
            that.dataForm = {
                id: null,
                username: '',
                password: '',
                name: '',
                sex: '',
                tel: '',
                email: '',
                job: '',
                roleIds: [],
                deptId: null,
                status: 1
            };
            that.dialogVisible = true;
            that.$nextTick(() => {
                that.$refs['dataForm'].clearValidate();
            });
        },
        updateHandle: function(row) {
            let that = this;
            that.dialogTitle = '修改用户';
            that.dataForm = {
                id: row.id,
                username: row.username,
                password: '',
                name: row.name,
                sex: row.sex,
                tel: row.tel,
                email: row.email,
                job: row.job,
                roleIds: row.roleIds || [],
                deptId: row.deptId,
                status: row.status
            };
            that.dialogVisible = true;
            that.$nextTick(() => {
                that.$refs['dataForm'].clearValidate();
            });
        },
        submitHandle: function() {
            let that = this;
            that.$refs['dataForm'].validate(valid => {
                if (valid) {
                    let data = {
                        id: that.dataForm.id,
                        username: that.dataForm.username,
                        password: that.dataForm.password,
                        name: that.dataForm.name,
                        sex: that.dataForm.sex,
                        tel: that.dataForm.tel,
                        email: that.dataForm.email,
                        job: that.dataForm.job,
                        roleIds: that.dataForm.roleIds,
                        deptId: that.dataForm.deptId,
                        status: that.dataForm.status
                    };
                    let url = that.dataForm.id ? 'user/updateUser' : 'user/insertUser';
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
            let ids = id ? [id] : that.dataListSelections.map(item => item.id);
            if (ids.length == 0) {
                ElMessage({
                    message: '没有选中记录',
                    type: 'warning',
                    duration: 1200
                });
            } else {
                ElMessageBox.confirm('确定要删除选中的记录？', '提示信息', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }).then(() => {
                    that.$http('user/deleteUserByIds', 'POST', ids, true, function(resp) {
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
        }
    },
    created: function() {
        this.loadDataList();
        this.loadRoleList();
        this.loadDeptList();
    }
};
</script>

<style></style>
VUEEOF; __tr_native_ec=$?; pwd -P >| '/var/folders/hn/1ylcxx294sz85pbtym3z3h880000gn/T/agent-toolhost/jobs/job-0d5f5336466b45e7b05ff5d5e72ed108/cwd.txt'; exit "$__tr_native_ec"